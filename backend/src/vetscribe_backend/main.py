import os

import uvicorn

from vetscribe_backend.app import create_app

app = create_app()


def run():
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8443")))


if __name__ == "__main__":
    run()
