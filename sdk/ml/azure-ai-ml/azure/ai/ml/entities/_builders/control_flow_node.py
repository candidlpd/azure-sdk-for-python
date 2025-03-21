# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
import re
import uuid
from abc import ABC
from typing import Dict, Union

from azure.ai.ml._utils.utils import is_data_binding_expression, is_internal_components_enabled
from azure.ai.ml.constants._common import CommonYamlFields
from azure.ai.ml.constants._component import ControlFlowType
from azure.ai.ml.entities._mixins import YamlTranslatableMixin
from azure.ai.ml.entities._validation import SchemaValidatableMixin
from azure.ai.ml.exceptions import ErrorTarget

from .._util import convert_ordered_dict_to_dict
from .base_node import BaseNode

module_logger = logging.getLogger(__name__)


# ControlFlowNode did not inherit from BaseNode since it doesn't have inputs/outputs like other nodes.
class ControlFlowNode(YamlTranslatableMixin, SchemaValidatableMixin, ABC):
    """
    Base class for control flow node in pipeline. Please do not directly use this class.
    """

    def __init__(self, **kwargs):
        # TODO(1979547): refactor this
        # property _source can't be set
        kwargs.pop("_source", None)
        _from_component_func = kwargs.pop("_from_component_func", False)
        self._type = kwargs.get("type", None)
        self._instance_id = str(uuid.uuid4())
        self.name = None
        if _from_component_func:
            # add current control flow node in pipeline stack for dsl scenario and remove the body from the pipeline
            # stack.
            self._register_in_current_pipeline_component_builder()

    @property
    def type(self):
        return self._type

    def _to_dict(self) -> Dict:
        return self._dump_for_validation()

    def _to_rest_object(self, **kwargs) -> dict:  # pylint disable=unused-argument
        """Convert self to a rest object for remote call."""
        rest_obj = self._to_dict()
        return convert_ordered_dict_to_dict(rest_obj)

    def _register_in_current_pipeline_component_builder(self):
        """Register this node in current pipeline component builder by adding
        self to a global stack."""
        from azure.ai.ml.dsl._pipeline_component_builder import _add_component_to_current_definition_builder

        _add_component_to_current_definition_builder(self)

    @classmethod
    def _get_validation_error_target(cls) -> ErrorTarget:
        """Return the error target of this resource.

        Should be overridden by subclass. Value should be in ErrorTarget
        enum.
        """
        return ErrorTarget.PIPELINE

    @classmethod
    def _from_rest_object(cls, obj: dict, reference_node_list: list) -> "ControlFlowNode":
        from azure.ai.ml.entities._job.pipeline._load_component import pipeline_node_factory

        node_type = obj.get(CommonYamlFields.TYPE, None)
        load_from_rest_obj_func = pipeline_node_factory.get_load_from_rest_object_func(_type=node_type)
        return load_from_rest_obj_func(obj, reference_node_list)


class LoopNode(ControlFlowNode, ABC):
    """
    Base class for loop node in pipeline. Please do not directly use this class.
    """

    def __init__(self, *, body: Union[BaseNode], **kwargs):
        self._body = body
        super(LoopNode, self).__init__(**kwargs)

    @property
    def body(self):
        return self._body

    def _register_in_current_pipeline_component_builder(self):
        """Register this node in current pipeline component builder by adding
        self to a global stack."""
        # pylint: disable=protected-access
        super(LoopNode, self)._register_in_current_pipeline_component_builder()
        self.body._set_referenced_control_flow_node_instance_id(self._instance_id)

    def _validate_body(self, raise_error=True):
        # pylint: disable=protected-access
        from .command import Command
        from .pipeline import Pipeline

        enable_body_type = (Command, Pipeline)
        if is_internal_components_enabled():
            from azure.ai.ml._internal.entities import Command as InternalCommand
            from azure.ai.ml._internal.entities import Pipeline as InternalPipeline

            enable_body_type = enable_body_type + (InternalCommand, InternalPipeline)

        validation_result = self._create_empty_validation_result()
        if not isinstance(self.body, enable_body_type):
            validation_result.append_error(
                yaml_path="body", message="Only command or pipeline job is supported as the body of control flow."
            )
        elif self._instance_id != self.body._referenced_control_flow_node_instance_id:
            # When the body is used in another loop node record the error message in validation result.
            validation_result.append_error("body", "The body of loop node cannot be promoted as another loop again.")
        return validation_result.try_raise(self._get_validation_error_target(), raise_error=raise_error)

    @staticmethod
    def _get_data_binding_expression_value(expression, regex):
        try:
            if is_data_binding_expression(expression):
                return re.findall(regex, expression)[0]

            return expression
        except Exception:  # pylint disable=broad-except
            module_logger.warning(f"Cannot get the value from data binding expression {expression}.")
            return expression

    @staticmethod
    def _is_loop_node_dict(obj):
        return obj.get(CommonYamlFields.TYPE, None) in [ControlFlowType.DO_WHILE]
