# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

# pylint: disable=protected-access,no-member

from typing import Dict, Union

from azure.ai.ml._restclient.v2022_06_01_preview.models import AutoMLJob as RestAutoMLJob
from azure.ai.ml._restclient.v2022_06_01_preview.models import ImageObjectDetection as RestImageObjectDetection
from azure.ai.ml._restclient.v2022_06_01_preview.models import JobBase, ObjectDetectionPrimaryMetrics, TaskType
from azure.ai.ml._utils._experimental import experimental
from azure.ai.ml._utils.utils import camel_to_snake, is_data_binding_expression
from azure.ai.ml.constants._job.automl import AutoMLConstants
from azure.ai.ml.constants._common import BASE_PATH_CONTEXT_KEY
from azure.ai.ml.entities._job._input_output_helpers import from_rest_data_outputs, to_rest_data_outputs
from azure.ai.ml.entities._job.automl.image.automl_image_object_detection_base import AutoMLImageObjectDetectionBase
from azure.ai.ml.entities._job.automl.image.image_limit_settings import ImageLimitSettings
from azure.ai.ml.entities._job.automl.image.image_sweep_settings import ImageSweepSettings
from azure.ai.ml.entities._job.identity import Identity
from azure.ai.ml.entities._util import load_from_dict


@experimental
class ImageObjectDetectionJob(AutoMLImageObjectDetectionBase):
    """Configuration for AutoML Image Object Detection job."""

    _DEFAULT_PRIMARY_METRIC = ObjectDetectionPrimaryMetrics.MEAN_AVERAGE_PRECISION

    def __init__(
        self,
        *,
        primary_metric: Union[str, ObjectDetectionPrimaryMetrics] = None,
        **kwargs,
    ) -> None:
        """Initialize a new AutoML Image Object Detection job.

        :param primary_metric: The primary metric to use for optimization
        :param kwargs: Job-specific arguments
        """
        # Extract any super class init settings
        limits = kwargs.pop("limits", None)
        sweep = kwargs.pop("sweep", None)
        training_parameters = kwargs.pop("training_parameters", None)
        search_space = kwargs.pop("search_space", None)

        super().__init__(
            task_type=TaskType.IMAGE_OBJECT_DETECTION,
            limits=limits,
            sweep=sweep,
            training_parameters=training_parameters,
            search_space=search_space,
            **kwargs,
        )

        self.primary_metric = primary_metric or ImageObjectDetectionJob._DEFAULT_PRIMARY_METRIC

    @property
    def primary_metric(self):
        return self._primary_metric

    @primary_metric.setter
    def primary_metric(self, value: Union[str, ObjectDetectionPrimaryMetrics]):
        if is_data_binding_expression(str(value), ["parent"]):
            self._primary_metric = value
            return
        self._primary_metric = (
            ImageObjectDetectionJob._DEFAULT_PRIMARY_METRIC
            if value is None
            else ObjectDetectionPrimaryMetrics[camel_to_snake(value).upper()]
        )

    def _to_rest_object(self) -> JobBase:
        image_object_detection_task = RestImageObjectDetection(
            target_column_name=self.target_column_name,
            training_data=self.training_data,
            validation_data=self.validation_data,
            validation_data_size=self.validation_data_size,
            limit_settings=self._limits._to_rest_object() if self._limits else None,
            sweep_settings=self._sweep._to_rest_object() if self._sweep else None,
            model_settings=self._training_parameters,
            search_space=(
                [entry._to_rest_object() for entry in self._search_space if entry is not None]
                if self._search_space is not None
                else None
            ),
            primary_metric=self.primary_metric,
            log_verbosity=self.log_verbosity,
        )
        # resolve data inputs in rest object
        self._resolve_data_inputs(image_object_detection_task)

        properties = RestAutoMLJob(
            display_name=self.display_name,
            description=self.description,
            experiment_name=self.experiment_name,
            tags=self.tags,
            compute_id=self.compute,
            properties=self.properties,
            environment_id=self.environment_id,
            environment_variables=self.environment_variables,
            services=self.services,
            outputs=to_rest_data_outputs(self.outputs),
            resources=self.resources,
            task_details=image_object_detection_task,
            identity=self.identity._to_rest_object() if self.identity else None,
        )

        result = JobBase(properties=properties)
        result.name = self.name
        return result

    @classmethod
    def _from_rest_object(cls, job_rest_object: JobBase) -> "ImageObjectDetectionJob":
        properties: RestAutoMLJob = job_rest_object.properties
        task_details: RestImageObjectDetection = properties.task_details

        job_args_dict = {
            "id": job_rest_object.id,
            "name": job_rest_object.name,
            "description": properties.description,
            "tags": properties.tags,
            "properties": properties.properties,
            "experiment_name": properties.experiment_name,
            "services": properties.services,
            "status": properties.status,
            "creation_context": job_rest_object.system_data,
            "display_name": properties.display_name,
            "compute": properties.compute_id,
            "outputs": from_rest_data_outputs(properties.outputs),
            "resources": properties.resources,
            "identity": Identity._from_rest_object(properties.identity) if properties.identity else None,
        }

        image_object_detection_job = cls(
            target_column_name=task_details.target_column_name,
            training_data=task_details.training_data,
            validation_data=task_details.validation_data,
            validation_data_size=task_details.validation_data_size,
            limits=(
                ImageLimitSettings._from_rest_object(task_details.limit_settings)
                if task_details.limit_settings
                else None
            ),
            sweep=(
                ImageSweepSettings._from_rest_object(task_details.sweep_settings)
                if task_details.sweep_settings
                else None
            ),
            training_parameters=task_details.model_settings,
            search_space=cls._get_search_space_from_str(task_details.search_space),
            primary_metric=task_details.primary_metric,
            log_verbosity=task_details.log_verbosity,
            **job_args_dict,
        )

        image_object_detection_job._restore_data_inputs()

        return image_object_detection_job

    @classmethod
    def _load_from_dict(
        cls,
        data: Dict,
        context: Dict,
        additional_message: str,
        inside_pipeline=False,
        **kwargs,
    ) -> "ImageObjectDetectionJob":
        from azure.ai.ml._schema.automl.image_vertical.image_object_detection import ImageObjectDetectionSchema
        from azure.ai.ml._schema.pipeline.automl_node import ImageObjectDetectionNodeSchema

        if inside_pipeline:
            if context.get("inside_pipeline", None) is None:
                context["inside_pipeline"] = True
            loaded_data = load_from_dict(
                ImageObjectDetectionNodeSchema,
                data,
                context,
                additional_message,
                **kwargs,
            )
        else:
            loaded_data = load_from_dict(ImageObjectDetectionSchema, data, context, additional_message, **kwargs)
        job_instance = cls._create_instance_from_schema_dict(loaded_data)
        return job_instance

    @classmethod
    def _create_instance_from_schema_dict(cls, loaded_data: Dict) -> "ImageObjectDetectionJob":
        loaded_data.pop(AutoMLConstants.TASK_TYPE_YAML, None)
        data_settings = {
            "training_data": loaded_data.pop("training_data"),
            "target_column_name": loaded_data.pop("target_column_name"),
            "validation_data": loaded_data.pop("validation_data", None),
            "validation_data_size": loaded_data.pop("validation_data_size", None),
        }
        job = ImageObjectDetectionJob(**loaded_data)
        job.set_data(**data_settings)
        return job

    def _to_dict(self, inside_pipeline=False) -> Dict:
        from azure.ai.ml._schema.automl.image_vertical.image_object_detection import ImageObjectDetectionSchema
        from azure.ai.ml._schema.pipeline.automl_node import ImageObjectDetectionNodeSchema

        if inside_pipeline:
            schema_dict = ImageObjectDetectionNodeSchema(
                context={BASE_PATH_CONTEXT_KEY: "./", "inside_pipeline": True}
            ).dump(self)
        else:
            schema_dict = ImageObjectDetectionSchema(context={BASE_PATH_CONTEXT_KEY: "./"}).dump(self)

        return schema_dict

    def __eq__(self, other) -> bool:
        if not isinstance(other, ImageObjectDetectionJob):
            return NotImplemented

        if not super().__eq__(other):
            return False

        return self.primary_metric == other.primary_metric

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
