# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from abc import ABC

from azure.ai.ml._restclient.v2022_06_01_preview.models import BanditPolicy as RestBanditPolicy
from azure.ai.ml._restclient.v2022_06_01_preview.models import EarlyTerminationPolicy as RestEarlyTerminationPolicy
from azure.ai.ml._restclient.v2022_06_01_preview.models import EarlyTerminationPolicyType
from azure.ai.ml._restclient.v2022_06_01_preview.models import MedianStoppingPolicy as RestMedianStoppingPolicy
from azure.ai.ml._restclient.v2022_06_01_preview.models import (
    TruncationSelectionPolicy as RestTruncationSelectionPolicy,
)
from azure.ai.ml.entities._mixins import RestTranslatableMixin
from azure.ai.ml.entities._util import camel_to_snake


class EarlyTerminationPolicy(ABC, RestTranslatableMixin):
    def __init__(
        self,
        *,
        delay_evaluation: int,
        evaluation_interval: int,
    ):
        self.type = None
        self.delay_evaluation = delay_evaluation
        self.evaluation_interval = evaluation_interval

    @classmethod
    def _from_rest_object(cls, obj: RestEarlyTerminationPolicy) -> "EarlyTerminationPolicy":
        if not obj:
            return None

        policy = None
        if obj.policy_type == EarlyTerminationPolicyType.BANDIT:
            policy = BanditPolicy._from_rest_object(obj)  # pylint: disable=protected-access

        if obj.policy_type == EarlyTerminationPolicyType.MEDIAN_STOPPING:
            policy = MedianStoppingPolicy._from_rest_object(obj)  # pylint: disable=protected-access

        if obj.policy_type == EarlyTerminationPolicyType.TRUNCATION_SELECTION:
            policy = TruncationSelectionPolicy._from_rest_object(obj)  # pylint: disable=protected-access

        return policy

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EarlyTerminationPolicy):
            return NotImplementedError
        return self._to_rest_object() == other._to_rest_object()


class BanditPolicy(EarlyTerminationPolicy):
    """Defines an early termination policy based on slack criteria, and a frequency and delay interval for evaluation.

    :param delay_evaluation: Number of intervals by which to delay the first evaluation.
    :type delay_evaluation: int
    :param evaluation_interval: Interval (number of runs) between policy evaluations.
    :type evaluation_interval: int
    :param slack_amount: Absolute distance allowed from the best performing run.
    :type slack_amount: float
    :param slack_factor: Ratio of the allowed distance from the best performing run.
    :type slack_factor: float
    """

    def __init__(
        self,
        *,
        delay_evaluation: int = 0,
        evaluation_interval: int = 0,
        slack_amount: float = 0,
        slack_factor: float = 0,
    ) -> None:
        super().__init__(delay_evaluation=delay_evaluation, evaluation_interval=evaluation_interval)
        self.type = EarlyTerminationPolicyType.BANDIT.lower()
        self.slack_factor = slack_factor
        self.slack_amount = slack_amount

    def _to_rest_object(self) -> RestBanditPolicy:
        return RestBanditPolicy(
            delay_evaluation=self.delay_evaluation,
            evaluation_interval=self.evaluation_interval,
            slack_factor=self.slack_factor,
            slack_amount=self.slack_amount,
        )

    @classmethod
    def _from_rest_object(cls, obj: RestBanditPolicy) -> "BanditPolicy":
        return cls(
            delay_evaluation=obj.delay_evaluation,
            evaluation_interval=obj.evaluation_interval,
            slack_factor=obj.slack_factor,
            slack_amount=obj.slack_amount,
        )


class MedianStoppingPolicy(EarlyTerminationPolicy):
    """Defines an early termination policy based on running averages of the primary metric of all runs.

    :param delay_evaluation: Number of intervals by which to delay the first evaluation.
    :type delay_evaluation: int
    :param evaluation_interval: Interval (number of runs) between policy evaluations.
    :type evaluation_interval: int
    """

    def __init__(
        self,
        *,
        delay_evaluation: int = 0,
        evaluation_interval: int = 0,
    ) -> None:
        super().__init__(delay_evaluation=delay_evaluation, evaluation_interval=evaluation_interval)
        self.type = camel_to_snake(EarlyTerminationPolicyType.MEDIAN_STOPPING)

    def _to_rest_object(self) -> RestMedianStoppingPolicy:
        return RestMedianStoppingPolicy(
            delay_evaluation=self.delay_evaluation, evaluation_interval=self.evaluation_interval
        )

    @classmethod
    def _from_rest_object(cls, obj: RestMedianStoppingPolicy) -> "MedianStoppingPolicy":
        return cls(
            delay_evaluation=obj.delay_evaluation,
            evaluation_interval=obj.evaluation_interval,
        )


class TruncationSelectionPolicy(EarlyTerminationPolicy):
    """Defines an early termination policy that cancels a given percentage of runs at each evaluation interval.

    :param delay_evaluation: Number of intervals by which to delay the first evaluation.
    :type delay_evaluation: int
    :param evaluation_interval: Interval (number of runs) between policy evaluations.
    :type evaluation_interval: int
    :param truncation_percentage: The percentage of runs to cancel at each evaluation interval.
    :type truncation_percentage: int
    """

    def __init__(
        self,
        *,
        delay_evaluation: int = 0,
        evaluation_interval: int = 0,
        truncation_percentage: int = 0,
    ) -> None:
        super().__init__(delay_evaluation=delay_evaluation, evaluation_interval=evaluation_interval)
        self.type = camel_to_snake(EarlyTerminationPolicyType.TRUNCATION_SELECTION)
        self.truncation_percentage = truncation_percentage

    def _to_rest_object(self) -> RestTruncationSelectionPolicy:
        return RestTruncationSelectionPolicy(
            delay_evaluation=self.delay_evaluation,
            evaluation_interval=self.evaluation_interval,
            truncation_percentage=self.truncation_percentage,
        )

    @classmethod
    def _from_rest_object(cls, obj: RestTruncationSelectionPolicy) -> "TruncationSelectionPolicy":
        return cls(
            delay_evaluation=obj.delay_evaluation,
            evaluation_interval=obj.evaluation_interval,
            truncation_percentage=obj.truncation_percentage,
        )
