from a2a.types import (
    TaskArtifactUpdateEvent,
    Task,
    TaskStatusUpdateEvent,
    AgentCard,
    TaskStatus,
    TaskState,
    Artifact,
)


class GenericTaskUpdateCallback:
    def __init__(self) -> None:
        self._task_id_to_task: dict[str, Task] = {}

    def task_callback(
        self,
        event: Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent,
        _: AgentCard,
    ) -> Task:
        if isinstance(event, Task):
            self._task_id_to_task[event.id] = event
            return event
        elif isinstance(event, TaskStatusUpdateEvent):
            return self._task_status_update_callback(event)
        elif isinstance(event, TaskArtifactUpdateEvent):
            return self._task_artifact_update_callback(event)
        else:
            raise ValueError("Unexpected task type")

    def _task_status_update_callback(self, event: TaskStatusUpdateEvent) -> Task:
        task = self._task_id_to_task.get(event.taskId)
        if task is None:
            task = Task(
                contextId=event.contextId,
                id=event.taskId,
                metadata=event.metadata,
                status=event.status,
            )
        else:
            task.status = event.status
            if task.metadata is None:
                task.metadata = event.metadata
            elif event.metadata is not None:
                task.metadata |= event.metadata

        self._task_id_to_task[event.taskId] = task
        return task

    def _task_artifact_update_callback(self, event: TaskArtifactUpdateEvent) -> Task:
        task = self._task_id_to_task.get(event.taskId)
        if task is None:
            task = Task(
                artifacts=[event.artifact],
                contextId=event.contextId,
                id=event.taskId,
                metadata=event.metadata,
                status=TaskStatus(state=TaskState.working),
            )
        else:
            if task.artifacts is None:
                task.artifacts = []

            if not event.append:  # append means appending to a previous artifact
                task.artifacts.append(event.artifact)
            else:
                current_artifact = self._get_artifact_by_id(
                    task.artifacts,
                    event.artifact.artifactId,
                )
                if current_artifact is None:
                    task.artifacts.append(event.artifact)
                else:
                    self._merge_artifacts(current_artifact, event.artifact)

        self._task_id_to_task[event.taskId] = task
        return task

    @staticmethod
    def _get_artifact_by_id(
        artifacts: list[Artifact] | None,
        artifact_id: str,
    ) -> Artifact | None:
        if artifacts is None:
            return None
        for artifact in artifacts:
            if artifact.artifactId == artifact_id:
                return artifact
        return None

    @staticmethod
    def _merge_artifacts(
        current_artifact: Artifact,
        new_artifact_data: Artifact,
    ) -> None:
        # parts
        current_artifact.parts.extend(new_artifact_data.parts)

        # metadata
        if current_artifact.metadata is None:
            current_artifact.metadata = new_artifact_data.metadata
        elif new_artifact_data.metadata is not None:
            current_artifact.metadata |= new_artifact_data.metadata

        # description
        if current_artifact.description is None:
            current_artifact.description = new_artifact_data.description

        # name
        if current_artifact.name is None:
            current_artifact.name = new_artifact_data.name
