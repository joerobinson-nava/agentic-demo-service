import shlex
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()


class CommandRequest(BaseModel):
    cmd: str


@app.post("/exec")
async def execute_command(request: CommandRequest):
    allowed_commands = ["ls", "pwd", "echo"]
    command = shlex.split(request.cmd)
    if command[0] not in allowed_commands:
        raise HTTPException(status_code=400, detail="Command not allowed")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return JSONResponse(content={"output": result.stdout})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))