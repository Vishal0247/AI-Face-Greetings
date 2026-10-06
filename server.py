import os
import sys
import cv2
import numpy as np
import base64

# Add the 'app' directory to the python path so absolute imports inside it work
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
sys.path.append(app_dir)

from flask import Flask, render_template_string, send_from_directory, Response, jsonify, request
from camera_app import CameraApp

# Initialize Flask App
# We set static_folder to the frontend directory so it can serve our css and js
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app = Flask(__name__, static_folder=frontend_dir)

# Initialize our AI logic
camera = CameraApp()

@app.route('/health')
def health():
    """Fast health check endpoint for Render — responds instantly."""
    return jsonify({"status": "ok"}), 200

@app.route('/')
def index():
    """Serve the main HTML interface."""
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve CSS, JS, and other static files."""
    return send_from_directory(frontend_dir, filename)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Receives base64 image from client, processes it, and returns state."""
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "No image provided"}), 400
        
    # Decode base64 image
    img_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
    img_bytes = base64.b64decode(img_data)
    
    # Convert to NumPy array and decode with OpenCV
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return jsonify({"error": "Invalid image"}), 400
        
    # Process frame
    camera.process_frame(frame)
    
    # Return updated state
    return jsonify(camera.get_state())

@app.route('/dashboard')
def dashboard():
    """Serve the Admin Dashboard."""
    return send_from_directory(frontend_dir, 'dashboard.html')

@app.route('/api/people')
def api_people():
    """Returns a list of all enrolled people and their photo counts."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "people")
    people = []
    
    if os.path.exists(data_dir):
        for name in os.listdir(data_dir):
            person_path = os.path.join(data_dir, name)
            if os.path.isdir(person_path):
                # Count files
                samples = len([f for f in os.listdir(person_path) if f.endswith('.jpg') or f.endswith('.png')])
                if samples > 0:
                    people.append({"name": name, "samples": samples})
                
    return jsonify(people)

@app.route('/api/people/<name>/photo')
def api_person_photo(name):
    """Serve a representative photo for an enrolled person."""
    person_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "people", name)
    if os.path.exists(person_dir):
        # Look for the first image
        for f in os.listdir(person_dir):
            if f.endswith('.jpg') or f.endswith('.png'):
                return send_from_directory(person_dir, f)
                
    # Return 404 if no photo found
    return "No photo found", 404

@app.route('/api/logs')
def api_logs():
    """Returns a list of recent scan video logs (gifs)."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs")
    logs = []
    
    if os.path.exists(log_dir):
        # Get all gifs, sort by modified time descending (newest first)
        files = [f for f in os.listdir(log_dir) if f.endswith('.gif')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
        
        # Return top 20
        for f in files[:20]:
            # Filename format: YYYY-MM-DD_HH-MM-SS_Name.gif
            parts = f.replace('.gif', '').split('_')
            name = parts[-1] if len(parts) > 1 else "Unknown"
            
            if name != "Unknown":
                date_time = parts[0] + " " + parts[1].replace("-", ":") if len(parts) > 2 else "Recent"
                logs.append({"filename": f, "name": name, "timestamp": date_time})
            
    return jsonify(logs)

@app.route('/api/people/<name>', methods=['DELETE'])
def delete_person(name):
    import shutil
    person_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "people", name)
    audio_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "audio", f"{name}.mp3")
    try:
        if os.path.exists(person_dir):
            try:
                import stat
                def remove_readonly(func, path, _):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(person_dir, onerror=remove_readonly)
            except Exception as e:
                print("Could not completely remove person dir, likely locked:", e)
        if os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception as e:
                print("Could not delete audio file, possibly locked by pygame:", e)
        
        # Delete associated logs
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs")
        if os.path.exists(log_dir):
            for f in os.listdir(log_dir):
                if f.endswith(f"_{name}.gif"):
                    try:
                        os.remove(os.path.join(log_dir, f))
                    except:
                        pass
                        
        # Retrain model
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "people")
        camera.recognizer.train(data_dir)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    import datetime
    
    stats = {
        "total_enrolled": 0,
        "scans_today": 0,
        "top_user": "None",
        "storage_used": "0 MB"
    }
    
    # 1. Total Enrolled
    people_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "people")
    if os.path.exists(people_dir):
        valid_people = 0
        for name in os.listdir(people_dir):
            person_path = os.path.join(people_dir, name)
            if os.path.isdir(person_path):
                samples = len([f for f in os.listdir(person_path) if f.endswith('.jpg') or f.endswith('.png')])
                if samples > 0:
                    valid_people += 1
        stats["total_enrolled"] = valid_people
        
    # 2. Scans Today & Top User
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs")
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    user_counts = {}
    total_size = 0
    
    if os.path.exists(log_dir):
        files = os.listdir(log_dir)
        for f in files:
            if f.endswith('.gif'):
                parts = f.replace('.gif', '').split('_')
                if len(parts) > 1:
                    name = parts[-1]
                    
                    if name != "Unknown":
                        # 2. Scans Today
                        if f.startswith(today_str):
                            stats["scans_today"] += 1
                        
                        # 3. Top User Count
                        user_counts[name] = user_counts.get(name, 0) + 1
                        
                # 4. Storage size
                file_path = os.path.join(log_dir, f)
                total_size += os.path.getsize(file_path)
                
    if user_counts:
        stats["top_user"] = max(user_counts, key=user_counts.get)
        
    stats["storage_used"] = f"{total_size / (1024 * 1024):.1f} MB"
    
    return jsonify(stats)

@app.route('/api/logs/<filename>')
def serve_log_video(filename):
    """Serve the generated log gifs."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs")
    return send_from_directory(log_dir, filename)

@app.route('/api/logs/<filename>', methods=['DELETE'])
def delete_log(filename):
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs")
    file_path = os.path.join(log_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route('/api/logs_all', methods=['DELETE'])
def delete_all_logs():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs")
    if os.path.exists(log_dir):
        for f in os.listdir(log_dir):
            if f.endswith('.gif'):
                os.remove(os.path.join(log_dir, f))
    return jsonify({"success": True})

@app.route('/audio/<name>')
def serve_audio(name):
    """Serve audio file for a person. Supports mp3, wav, m4a, ogg, webm."""
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "audio")
    supported_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.aac', '.flac']
    
    for ext in supported_extensions:
        filename = f"{name}{ext}"
        filepath = os.path.join(audio_dir, filename)
        if os.path.exists(filepath):
            return send_from_directory(audio_dir, filename)
    
    return "No audio found", 404

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    """API endpoint to upload a custom audio greeting for a person. Accepts any audio format."""
    name = request.form.get('name')
    file = request.files.get('file')
    
    if not name or not file:
        return jsonify({"success": False, "message": "Name and audio file are required."}), 400
    
    try:
        audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        # Get the original file extension
        original_filename = file.filename or "audio.mp3"
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.mp3'
        
        # Delete ALL old audio files for this person (any format)
        supported_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.aac', '.flac']
        for old_ext in supported_extensions:
            old_path = os.path.join(audio_dir, f"{name}{old_ext}")
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
        
        # Save with original extension
        audio_path = os.path.join(audio_dir, f"{name}{ext}")
        file.save(audio_path)
        return jsonify({"success": True, "message": f"Custom audio ({ext}) saved for {name}!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/status')
def status():
    """JSON API endpoint for the frontend to poll real-time status."""
    return jsonify(camera.get_state())

@app.route('/start_enrollment', methods=['POST'])
def start_enrollment():
    """API endpoint to trigger enrollment from the web UI (Live camera)."""
    data = request.json
    name = data.get('name')
    if name:
        camera.enroll_manager.start_enrollment(name)
        return jsonify({"success": True, "message": f"Started enrollment for {name}"})
    return jsonify({"success": False, "message": "No name provided"}), 400

@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    """API endpoint to upload a photo for enrollment."""
    name = request.form.get('name')
    file = request.files.get('file')
    
    if not name or not file:
        return jsonify({"success": False, "message": "Name and file are required."}), 400
        
    try:
        # Read the file and convert to numpy array
        np_arr = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"success": False, "message": "Invalid image file."}), 400
            
        success, message = camera.enroll_from_image(name, frame)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/cancel_enrollment', methods=['POST'])
def cancel_enrollment():
    """API endpoint to cancel enrollment."""
    camera.enroll_manager.is_enrolling = False
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("==================================================")
    print(f"   AI FACE GREETING WEB SERVER STARTED")
    print(f"   Listening on port {port}")
    print("==================================================")
    
    try:
        from waitress import serve
        print("   Running in PRODUCTION MODE via Waitress WSGI")
        serve(app, host='0.0.0.0', port=port, threads=8)
    except ImportError:
        print("   [WARN] Waitress not installed. Falling back to dev server.")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    finally:
        camera.release()
