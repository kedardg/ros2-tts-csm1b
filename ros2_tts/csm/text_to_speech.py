import os
import yaml
import torch
import torchaudio
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from huggingface_hub import hf_hub_download
from ros2_tts.csm.generator import load_csm_1b, Segment

@dataclass
class SpeakerPrompt:
    text: str
    audio_path: str
    speaker_id: int
    audio: Optional[torch.Tensor] = None

class TextToSpeechGenerator:
    def __init__(self, settings_path: str):
        # Load settings
        with open(settings_path, 'r') as f:
            self.settings = yaml.safe_load(f)
        
        # Create required directories
        for dir_path in [
            self.settings['paths']['output_dir'],
            self.settings['paths'].get('prompt_dir', 'prompts')  # Make prompt_dir optional
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize generator with settings
        self.generator = load_csm_1b(
            device=self.settings['model']['device'],
            settings=self.settings
        )
        
        # Load speaker prompt if enabled
        if self.settings['model']['use_speaker_prompt']:
            self.speaker_prompt = self.load_speaker_prompt()
        else:
            self.speaker_prompt = None

    def load_audio_file(self, audio_path: str) -> torch.Tensor:
        """Load and resample audio file to target sample rate."""
        audio_tensor, sample_rate = torchaudio.load(audio_path)
        audio_tensor = audio_tensor.squeeze(0)
        if sample_rate != self.settings['audio']['sample_rate']:
            audio_tensor = torchaudio.functional.resample(
                audio_tensor, 
                orig_freq=sample_rate,
                new_freq=self.settings['audio']['sample_rate']
            )
        return audio_tensor

    def load_speaker_prompt(self) -> Optional[SpeakerPrompt]:
        """Load the speaker prompt defined in settings if available."""
        if 'speaker_prompt' not in self.settings:
            print("No speaker prompt configuration found in settings")
            return None
            
        config = self.settings['speaker_prompt']
        
        # Download or use local audio file
        if config['audio_path'].startswith('http'):
            audio_path = hf_hub_download(
                repo_id=self.settings['model']['repo_id'],
                filename=config['audio_path']
            )
        else:
            audio_path = config['audio_path']
            
        if not os.path.exists(audio_path):
            print(f"Warning: Speaker prompt audio file not found at {audio_path}")
            return None
        
        try:
            # Create prompt object
            prompt = SpeakerPrompt(
                text=config['text'],
                audio_path=audio_path,
                speaker_id=config['speaker_id']
            )
            
            # Load audio
            prompt.audio = self.load_audio_file(audio_path)
            return prompt
            
        except Exception as e:
            print(f"Error loading speaker prompt: {str(e)}")
            return None

    def generate_speech(self, text: str, output_filename: str) -> None:
        """Generate speech from text, with or without speaker prompt."""
        # Prepare context and speaker_id based on whether we're using a prompt
        context = []
        speaker_id = 0  # default speaker ID
        
        if self.speaker_prompt:
            context = [Segment(
                text=self.speaker_prompt.text,
                speaker=self.speaker_prompt.speaker_id,
                audio=self.speaker_prompt.audio
            )]
            speaker_id = self.speaker_prompt.speaker_id
        
        print(f"Generating speech for text: {text}")
        audio_tensor = self.generator.generate(
            text=text,
            speaker=speaker_id,
            context=context,
            max_audio_length_ms=self.settings['audio']['max_audio_length_ms']
        )
        
        # Save the generated audio
        output_path = os.path.join(self.settings['paths']['output_dir'], output_filename)
        torchaudio.save(
            output_path,
            audio_tensor.unsqueeze(0).cpu(),
            self.generator.sample_rate
        )
        print(f"Audio saved to: {output_path}")

    def process_text_file(self, input_file: str) -> None:
        """Process a text file and generate speech for each line."""
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line:  # Skip empty lines
                output_filename = f"output_{i+1}.wav"
                self.generate_speech(line, output_filename)

def main():
    # Initialize generator with settings
    generator = TextToSpeechGenerator('settings.yaml')
    
    # Example usage
    input_file = "input.txt"
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found")
        return
    
    generator.process_text_file(input_file)

if __name__ == "__main__":
    main() 