import mlflow
import os

def save_prompt_to_mlflow(prompt, response, model):
    mlflow.set_tracking_uri("http://mlflow:5000")
    experiment_name = "UniversityAssistant"
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        mlflow.create_experiment(experiment_name)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run():
        mlflow.log_param("prompt", prompt)
        mlflow.log_param("response", response)
        mlflow.log_param("model", model)
        with open("prompt.txt", "w") as f:
            f.write(prompt)
        mlflow.log_artifact("prompt.txt")
        os.remove("prompt.txt")
