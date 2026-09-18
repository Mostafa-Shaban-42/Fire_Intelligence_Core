from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PT_PATH = PROJECT_ROOT / "models" / "best.pt"
ONNX_OUT_PATH = PROJECT_ROOT / "models" / "fire_detector.onnx"

def export_to_onnx():
    pt_path = MODEL_PT_PATH
    if not pt_path.exists():
        alt_pt = PROJECT_ROOT / "weights" / "best.pt"
        if alt_pt.exists():
            pt_path = alt_pt
        else:
            raise FileNotFoundError(f"Model .pt file not found at {MODEL_PT_PATH} or {alt_pt}")

    print(f"🚀 Exporting YOLO model from {pt_path} to ONNX Runtime...")
    model = YOLO(str(pt_path))
    
    # Export with graph simplification for sub-millisecond inference
    model.export(
        format="onnx",
        imgsz=640,
        dynamic=True,
        simplify=True,
        opset=12
    )
    print("✅ Model successfully exported to ONNX format!")

if __name__ == "__main__":
    export_to_onnx()