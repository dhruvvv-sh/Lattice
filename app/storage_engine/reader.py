from fastapi.responses import FileResponse

def read_file(filepath:str):
    return FileResponse(
        path = filepath,
        filename=filepath.split("\\")[-1]
    )