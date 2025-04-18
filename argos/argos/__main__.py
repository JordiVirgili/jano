if __name__ == "__main__":
    import uvicorn
    import argparse
    from .main import app

    parser = argparse.ArgumentParser(description="Init server")

    parser.add_argument("-p", "--port", type=int, default=8005, help="Port to deploy (default 8005)")

    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port, loop="asyncio")