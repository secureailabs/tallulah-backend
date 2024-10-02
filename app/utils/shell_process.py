import asyncio
import subprocess
from typing import List, Optional

from pydantic import BaseModel


class ShellProcessResult(BaseModel):
    status: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None


async def run_shell_code(code: str) -> ShellProcessResult:
    # run the code and capture the output and errors

    proc = await asyncio.create_subprocess_shell(
        code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    # If no exception, print the output
    return ShellProcessResult(status=proc.returncode, output=stdout.decode(), error=stderr.decode())
