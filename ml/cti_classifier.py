import os
import pandas as pd
import joblib
import platform
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Heuristic keyword list (for quick labelling before training)
CTI_KEYWORDS = [
    "CVE", "vulnerability", "exploit", "attack", "malware", "ransomware",
    "phishing", "zero-day", "APT", "hackers", "breach", "data leak", "botnet",
    "trojan", "spyware", "patch", "vulnerabilities"
]

MODEL_PATH = "ml/cti_classifier_model.pkl"
VECTORIZER_PATH = "ml/tfidf_vectorizer.pkl"


def label_message(text):
    """Keyword-based heuristic labelling for bootstrap training data."""
    if not isinstance(text, str):
        return "Non-CTI"
    text_lower = text.lower()
    return "CTI" if any(k.lower() in text_lower for k in CTI_KEYWORDS) else "Non-CTI"


def prepare_training_data(df, text_column="Content"):
    """Apply keyword heuristic to generate labels."""
    df["Label"] = df[text_column].apply(label_message)
    return df


def train_and_save_model(df, text_column="Content", label_column="Label"):
    """Train TF-IDF + Logistic Regression classifier and save it."""
    X = df[text_column].astype(str)
    y = df[label_column]

    vectorizer = TfidfVectorizer(max_features=1000)
    X_vec = vectorizer.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("📊 Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save model + vectorizer
    os.makedirs("ml", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    return model, vectorizer


def load_model_and_vectorizer():
    """Load model + vectorizer from disk."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        raise FileNotFoundError("CTI classifier model/vectorizer not found. Train first.")

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return model, vectorizer


def predict_messages(messages):
    """Predict CTI vs Non-CTI for a list of messages."""
    try:
        model, vectorizer = load_model_and_vectorizer()
    except FileNotFoundError:
        print("⚠️ No trained model found. Training a new one...")
        df = pd.DataFrame({"Content": messages})
        df = prepare_training_data(df, text_column="Content")
        model, vectorizer = train_and_save_model(df, text_column="Content", label_column="Label")

    X_vec = vectorizer.transform(messages)
    preds = model.predict(X_vec)
    return preds


def save_labeled_dataframe(df, filename="labeled_output.xlsx"):
    """
    Save the labeled DataFrame to Excel and auto-open depending on OS.
    """
    df.to_excel(filename, index=False)
    print(f"✅ Labeled data saved to {filename}")

    # Try to open file automatically
    try:
        if platform.system() == "Windows":
            os.startfile(filename)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{filename}'")
        elif platform.system() == "Linux":
            os.system(f"xdg-open '{filename}'")
        else:
            print("⚠️ Unsupported OS for auto-opening the file.")
    except Exception as e:
        print(f"⚠️ Could not auto-open file: {e}")