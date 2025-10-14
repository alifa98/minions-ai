from langgraph.checkpoint.memory import MemorySaver

import config


# from psycopg_pool import ConnectionPool
# from langchain_postgres import (
#     PostgresCheckpoint, PickleCheckpointSerializer
# )


def get_checkpointer():
    """Get the checkpointer instance based on the environment."""

    setting = config.get_settings()
    if setting.checkpointer == "postgres":
        # pool = ConnectionPool(
        #     # Example configuration
        #     conninfo="postgresql://user:password@localhost:5432/dbname",
        #     max_size=20,
        # )
        # return PostgresCheckpoint(
        #     serializer=PickleCheckpointSerializer(),
        #     sync_connection=pool,
        # )
        raise NotImplementedError()
    else:
        return MemorySaver()  # Fallback to in-memory checkpointer
