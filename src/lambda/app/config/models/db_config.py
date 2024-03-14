from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DbConfig:
    provider: str
    table_name: str
    config_item_key_id: str

    @staticmethod
    def from_dict(item: dict):
        """
        Converts dictionary to DbConfig object

        Example:
        {
            "provider": "<name_of_db_provider>",
            "table_name": "<dynamo_table_name>",
            "config_item_key_id": "<dynamo_table_key_id>"
        }
        """
        return DbConfig(**item)
