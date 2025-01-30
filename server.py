import uvicorn

if __name__ == '__main__':
    uvicorn.run("web_app:create_app", reload=True, port=8137, host='82.147.84.128')
    # uvicorn.run("web_app:create_app", reload=True, port=8137)

