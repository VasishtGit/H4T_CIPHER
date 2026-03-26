import torch
import torch.nn as nn
from torchvision import transforms

class GraphSolverNet(nn.Module):
    def __init__(self):
        super().__init__()
        # This architecture must match your .pth file exactly.
        # Example using a standard ResNet18 backbone:
        self.backbone = torch.hub.load('pytorch/vision', 'resnet18', pretrained=False)
        self.backbone.fc = nn.Linear(512, 128) # Adjust based on your model output

    def forward(self, x):
        # The actual forward pass through the network layers
        return self.backbone(x)

class ModelManager:
    def __init__(self, weights_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = GraphSolverNet().to(self.device)
        
        # Load the pre-trained weights
        self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.model.eval() # Set to evaluation mode for inference

    def run_inference(self, cv2_img):
        # 1. Preprocessing: Convert image to tensor and move to RTX 3050
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        input_tensor = transform(cv2_img).unsqueeze(0).to(self.device)

        # 2. Executing the Forward Pass
        with torch.no_grad(): # Disable gradient calculation to save VRAM
            output = self.model(input_tensor) 
            return output