import argparse
from pathlib import Path

import joblib
import numpy as np
import yaml

from utils.model_conversion import convert_model
from utils.model_installation import install_model


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare Shapeshifter for Tofino.")
    parser.add_argument("--config", type=str, required=True, help="Configuration to use.")
    parser.add_argument("--tcam", action="store_true", help="Use the TCAM implementation.")
    return parser.parse_args()


def load_config(config_name):
    config_path = Path(__file__).resolve().parent / "configs" / f"{config_name}.yaml"
    with config_path.open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def load_model(model_name):
    models_dir = Path(__file__).resolve().parent / "models"
    model = joblib.load(models_dir / f"{model_name}.joblib")
    label_encoder = joblib.load(models_dir / f"{model_name}_label_encoder.joblib")
    selector = joblib.load(models_dir / f"{model_name}_selector.joblib")
    return model, label_encoder, selector


def load_dataset(dataset_name):
    dataset_path = Path(__file__).resolve().parent / "datasets" / dataset_name / "X_test.npy"
    return np.load(dataset_path)


def prepare(model, config, tcam, *, selector, label_encoder, model_name, X_test):
    # model conversion
    output_path = Path(__file__).resolve().parent / "x" / f"{model_name}.py"
    conversion = convert_model(
        model=model, config=config, tcam=tcam,
        selector=selector, label_encoder=label_encoder, output_path=output_path,
    )

    # model installation
    install_model(conversion=conversion)

    return conversion


if __name__ == "__main__":
    args = parse_args()
    config = load_config(args.config)
    model, label_encoder, selector = load_model(config["model"])
    X_test = load_dataset(config["dataset"])

    prepare(
        model=model, config=config, tcam=args.tcam,
        selector=selector, label_encoder=label_encoder, model_name=f"{args.config}_{config['model']}",
        X_test=X_test,
    )
