import os
import sys
import subprocess
import wave
import struct


def check_pygame_installation():
    """Check if pygame is installed, and if not, install it."""
    try:
        import pygame

        print("✓ Pygame is already installed.")
    except ImportError:
        print("✗ Pygame is not installed. Installing now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
            print("✓ Pygame installed successfully.")
        except Exception as e:
            print(f"✗ Failed to install Pygame: {e}")
            print("Please install Pygame manually using: pip install pygame")
            return False
    return True


def create_sound_placeholders():
    """Create empty sound files if they don't exist."""
    sounds_dir = os.path.join("assets", "sounds")
    os.makedirs(sounds_dir, exist_ok=True)

    sound_files = [
        "select.wav",
        "jump.wav",
        "shoot.wav",
        "hit.wav",
        "enemy_hit.wav",
        "level_complete.wav",
    ]

    # Generate simple sound files using wave module instead of pygame
    for sound_file in sound_files:
        sound_path = os.path.join(sounds_dir, sound_file)
        if not os.path.exists(sound_path):
            print(f"Creating placeholder sound: {sound_file}")
            # Create a very simple beep sound
            create_simple_beep(sound_path)


def create_simple_beep(filename, duration=0.2, frequency=440.0, volume=0.5):
    """Create a simple beep sound file."""
    # Audio parameters
    sample_rate = 44100  # Hz
    num_samples = int(duration * sample_rate)

    # Create the audio data
    audio_data = []
    for i in range(num_samples):
        # Generate sine wave
        value = int(
            volume
            * 32767.0
            * struct.unpack(
                "<h",
                struct.pack(
                    "<H", int(32767 * (0.5 + 0.5 * frequency * i / sample_rate % 1.0))
                ),
            )[0]
            / 32767.0
        )
        audio_data.append(value)

    # Convert to bytes
    packed_audio = struct.pack("<" + ("h" * len(audio_data)), *audio_data)

    # Write to WAV file
    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(packed_audio)


def check_directory_structure():
    """Check if all required directories exist."""
    required_dirs = ["assets", "assets/images", "assets/sounds", "game"]

    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"Creating missing directory: {directory}")
            os.makedirs(directory, exist_ok=True)


def main():
    """Main setup function."""
    print("Setting up Muscle Baby Mayhem...")

    # Check for pygame
    if not check_pygame_installation():
        return

    # Check directory structure
    check_directory_structure()

    # Create sound placeholders
    create_sound_placeholders()

    print("\nSetup complete! You can now run the game with: python main.py")


if __name__ == "__main__":
    main()
