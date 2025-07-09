import os, uuid, glob, zipfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from threading import Thread
from pipeline import run_generation_pipeline
from job_store_redis import job_store

app = FastAPI()

class TopicInput(BaseModel):
    topic: str

@app.get("/")
def root():
    return {"message": "Backend is alive 🔥 Welcome to Learning Intelligent"}

@app.get("/download-part/{part}/{uid}")
def download_part_files(part: str, uid: str):
    base_dir = os.path.join(os.getcwd(), "Results", part)

    if not os.path.exists(base_dir):
        raise HTTPException(status_code=404, detail=f"Directory not found: {base_dir}")

    # 🔐 Define lock file path
    lockfile_path = os.path.join(base_dir, f"{uid}_{part}.lock")

    # 🔐 Check if a lock file already exists
    if os.path.exists(lockfile_path):
        raise HTTPException(status_code=429, detail="Another download is already in progress. Please try again shortly.")

    # 🔐 Create lock file to indicate processing
    try:
        with open(lockfile_path, 'w') as lockfile:
            lockfile.write("locked")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lock file: {str(e)}")

    # ✅ Only include PDFs that match UID
    pdf_pattern = os.path.join(base_dir, f"{uid}*.pdf")
    pdf_files = glob.glob(pdf_pattern)

    if not pdf_files:
        # Clean up lock file if no PDFs found
        if os.path.exists(lockfile_path):
            os.remove(lockfile_path)
        raise HTTPException(status_code=404, detail="No PDF files found for this UID and part")

    # 🧹 Find ALL files starting with uid_ for later deletion
    delete_pattern = os.path.join(base_dir, f"{uid}*")
    all_matching_files = glob.glob(delete_pattern)

    # 🗜️ Create ZIP archive
    zip_filename = f"{uid}_{part}_{uuid.uuid4().hex[:6]}.zip"
    zip_path = os.path.join(base_dir, zip_filename)

    try:
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for file_path in pdf_files:
                filename = os.path.basename(file_path)
                arcname = filename.replace(f"{uid}", "")
                zipf.write(file_path, arcname=arcname)
    except Exception as e:
        # Clean up lock on failure
        if os.path.exists(lockfile_path):
            os.remove(lockfile_path)
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {str(e)}")

    # 🧹 Background cleanup
    def cleanup():
        try:
            print(f"🧹 Deleting files: {all_matching_files}")
            for file_path in all_matching_files:
                os.remove(file_path)

            os.remove(zip_path)
            print(f"🧹 Deleted ZIP: {zip_path}")

        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")

        # 🔐 Always remove the lock file, even if cleanup fails
        if os.path.exists(lockfile_path):
            os.remove(lockfile_path)
            print(f"🔓 Lock file removed: {lockfile_path}")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{part}_{uid}.zip",
        background=BackgroundTask(cleanup)
    )

@app.get("/status/{uid}")
def getStatus(uid: str):
    try:
        statuses = {}
        for part in ["PartA", "PartB1", "PartB2"]:
            part_uid = uid + part
            job = job_store.get_job(part_uid)
            statuses[part] = job if job else {"status": "Pending"}
        return {"uid": uid, "statuses": statuses}
    except Exception as e:
        print(f"Error checking status for UID {uid}: {e}")
        return JSONResponse(status_code=500, content={"message": "Error checking status"})

@app.post("/generate")
def generate(input_data: TopicInput):
    uid = uuid.uuid4().hex[:6]
    for part in ["PartA", "PartB1", "PartB2"]:
        part_uid = uid + part
        job_store.create_job(part_uid,{"status": "Start generation"})
        thread = Thread(target=run_generation_pipeline, args=(input_data.topic, part_uid, part))
        thread.start()
    return {"uid": uid}