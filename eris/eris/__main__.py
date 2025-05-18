if __name__ == "__main__":
    import uvicorn
    import argparse
    from .main import app

    parser = argparse.ArgumentParser(description="Init Eris server")

    parser.add_argument("-p", "--port", type=int, default=8006, help="Port to deploy (default 8006)")

    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port, loop="asyncio")