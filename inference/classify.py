from inference.audio import AudioClassifier
import requests
import os


def classify_and_upload(file_path: str, qid: str) -> bool:
    print("Classifying " + file_path + " with qid " + qid)
    try:
        file = open(file_path, "rb")
        answer = requests.get(
            "{}/answer_full/{}".format(os.environ.get("BACKEND_URL"), qid)
        ).json()["answer"]
        f = file.read()
        result = AudioClassifier.predict(f, answer)
        file.seek(0)
        f = file.read()
        files = {"file": f}
        try:
            requests.post(
                url="{}/audio".format(os.environ.get("BACKEND_URL")),
                files=files,
                data={
                    "recType": "answer",
                    "correct": result,
                    "expectedAnswer": answer,
                    "transcript": "",
                },
            )
        except:
            pass
        return result
    except:
        return False
