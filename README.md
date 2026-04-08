# H4T Cipher

An AI-powered educational platform that helps students understand complex mathematical problems through intelligent analysis, step-by-step solutions, and animated video explanations.

## Features

- **Image-based Problem Input**: Upload images of mathematical problems for analysis
- **AI-Powered Description**: Extract and interpret text from uploaded images using advanced vision models
- **Intelligent Solutions**: Generate detailed, step-by-step solutions using AI tutoring
- **Animated Explanations**: Create custom Manim animations to visualize mathematical concepts
- **User Authentication**: Secure user management with Supabase
- **Real-time Chat**: Interactive doubt-clearing chat interface
- **Responsive Web Interface**: Modern, accessible frontend built with vanilla HTML/CSS/JavaScript

## Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **OpenRouter API**: Access to multiple AI models for problem analysis and solving
- **Manim**: Mathematical animation engine for video generation
- **Supabase**: Backend-as-a-Service for authentication and file storage
- **Python**: Core programming language

### Frontend
- **HTML5/CSS3**: Semantic markup and modern styling
- **Vanilla JavaScript**: No frameworks, lightweight and fast
- **Responsive Design**: Mobile-first approach with custom CSS

## Project Structure

```
H4T_CIPHER/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── Auth/
│   │   └── main.py          # Authentication service
│   ├── Gen_video/
│   │   ├── main.py          # Video generation service
│   │   ├── video_generator.py
│   │   └── final_videos/    # Generated video storage
│   └── Main/
│       └── main.py          # Main API service
├── frontend/
│   ├── index.html
│   ├── doubt chat/          # Interactive chat interface
│   ├── explanation page/    # Solution display page
│   ├── homepage/            # Image upload interface
│   ├── login/               # User authentication
│   └── signin/              # User registration
```

## Prerequisites

- Python 3.8+
- Node.js (for local development server)
- Supabase account
- OpenRouter API key

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd H4T_CIPHER
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the `backend` directory:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   SESSION_COOKIE_NAME=h4t_session
   SUPABASE_IMAGE_BUCKET=Image
   SUPABASE_VIDEO_BUCKET=Videos
   DESCRIPTION_MODEL_NAME=nvidia/nemotron-nano-12b-v2-vl:free
   SOLVER_MODEL_NAME=nvidia/nemotron-3-super-120b-a12b:free
   ```

4. **Start the backend services**

   Open separate terminals for each service:

   ```bash
   # Authentication service
   cd backend/Auth
   python main.py

   # Main API service
   cd backend/Main
   python main.py

   # Video generation service
   cd backend/Gen_video
   python main.py
   ```

5. **Start the frontend**

   ```bash
   cd frontend
   python -m http.server 5500  # Or use any local server
   ```

   Open `http://localhost:5500` in your browser.

## Usage

1. **Register/Login**: Create an account or sign in
2. **Upload Problem**: Select and upload an image of a mathematical problem
3. **Get Analysis**: The AI analyzes the image and provides a structured description
4. **View Solution**: Receive step-by-step solution with detailed explanations
5. **Watch Animation**: View custom-generated Manim animations explaining the concepts
6. **Ask Questions**: Use the doubt chat to clarify any remaining questions

## API Endpoints

### Authentication Service (Port 8001)
- `POST /signup` - User registration
- `POST /login` - User login
- `POST /logout` - User logout

### Main API Service (Port 8000)
- `POST /upload` - Upload and analyze mathematical problem images
- `GET /solution/{task_id}` - Get solution for a processed task

### Video Generation Service (Port 8002)
- `POST /generate-video` - Generate Manim animation videos
- `GET /video/{video_id}` - Retrieve generated videos

## Development

### Running Tests
```bash
# Add test commands when implemented
```

### Building for Production
```bash
# Add build commands when implemented
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenRouter for providing access to advanced AI models
- Manim Community for the mathematical animation library
- Supabase for backend infrastructure
- FastAPI for the web framework