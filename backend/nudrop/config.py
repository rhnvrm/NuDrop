from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "NuDrop"
    nucypher_network: str = 'lynx'
    provider_uri: str = "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b"
    seednode_uri: str = "https://lynx.nucypher.network:9151"

    class Config:
        env_file = ".env"

settings = Settings()