# Customization Guide

Advanced customization options for your video automation system.

## Table of Contents
1. [Script Generation](#script-generation)
2. [Video Creation](#video-creation)
3. [Platform-Specific Posting](#platform-specific-posting)
4. [Scheduling](#scheduling)
5. [Adding New Platforms](#adding-new-platforms)

---

## Script Generation

### Customize OpenAI Prompts

Edit the `_create_prompt()` method in `ScriptGenerator` class:

```python
def _create_prompt(self, product_data: Dict, platform: str) -> str:
    """Create a prompt based on product data and platform"""
    
    # Add your custom fields
    product_name = product_data.get('name', 'Product')
    description = product_data.get('description', '')
    price = product_data.get('price', '')
    features = product_data.get('features', '').split(',')  # NEW
    target_audience = product_data.get('audience', 'general')  # NEW
    
    # Customize per platform
    platform_specs = {
        "youtube": {
            "duration": "60-90 second",
            "style": "detailed and informative",
            "cta": "Subscribe and click the link in description"
        },
        "instagram": {
            "duration": "30-60 second",
            "style": "trendy and visual",
            "cta": "Double tap and save this post"
        },
        "pinterest": {
            "duration": "15-30 second",
            "style": "inspirational and aesthetic",
            "cta": "Pin this for later"
        },
        "twitter": {
            "duration": "15-30 second",
            "style": "punchy and engaging",
            "cta": "Retweet if you agree"
        }
    }
    
    spec = platform_specs.get(platform.lower(), platform_specs["youtube"])
    
    # Your custom prompt template
    prompt = f"""
Create a {spec['duration']} {spec['style']} video script for:

Product: {product_name}
Description: {description}
Price: {price}
Key Features: {', '.join(features)}
Target Audience: {target_audience}

Script Style Guidelines:
- Open with a hook that grabs {target_audience} attention
- Highlight these features: {', '.join(features[:3])}
- Use conversational tone
- Include price mention: {price}
- End with CTA: {spec['cta']}

Additional Requirements:
- Keep it natural for text-to-speech
- Use short sentences
- Include emotional appeal
- Add urgency if appropriate

Format as natural spoken dialogue only.
"""
    return prompt
```

### Different Scripts Per Platform

Generate unique scripts for each platform:

```python
def process_product(self, product_data: Dict, row_index: int):
    """Process a single product"""
    
    # Generate different scripts for different platforms
    scripts = {}
    for platform in ['youtube', 'instagram', 'pinterest', 'twitter']:
        scripts[platform] = self.script_generator.generate_script(
            product_data, 
            platform=platform
        )
    
    # Create different videos for different platforms
    videos = {}
    for platform, script in scripts.items():
        video_config = self._get_video_config(platform)
        videos[platform] = self.heygen_client.create_video(
            script, 
            product_data,
            config=video_config
        )
    
    # Post appropriate video to each platform
    # ... rest of code
```

### Add Brand Voice

Create a brand voice template:

```python
class BrandedScriptGenerator(ScriptGenerator):
    """Script generator with brand voice"""
    
    def __init__(self, api_key: str, brand_voice: str):
        super().__init__(api_key)
        self.brand_voice = brand_voice
    
    def generate_script(self, product_data: Dict, platform: str = "general") -> str:
        """Generate script with brand voice"""
        
        base_prompt = self._create_prompt(product_data, platform)
        
        # Add brand voice
        branded_prompt = f"""
{base_prompt}

Brand Voice & Style:
{self.brand_voice}

Ensure the script matches this brand personality and tone.
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a brand copywriter. Brand voice: {self.brand_voice}"
                },
                {"role": "user", "content": branded_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
```

Usage:

```python
brand_voice = """
- Friendly and approachable
- Use casual language
- Include humor where appropriate
- Emphasize sustainability and quality
- Target millennials and Gen Z
"""

script_generator = BrandedScriptGenerator(api_key, brand_voice)
```

---

## Video Creation

### Customize HeyGen Settings

Edit `HeyGenClient.create_video()` method:

```python
def create_video(self, script: str, product_data: Dict, config: Dict = None) -> Dict:
    """Create video with custom configuration"""
    
    # Default config
    default_config = {
        "avatar_id": "default_avatar",
        "voice_id": "en-US-JennyNeural",
        "background_color": "#FFFFFF",
        "aspect_ratio": "16:9",
        "width": 1920,
        "height": 1080
    }
    
    # Merge with provided config
    if config:
        default_config.update(config)
    
    payload = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": default_config["avatar_id"],
                "avatar_style": "normal"
            },
            "voice": {
                "type": "text",
                "input_text": script,
                "voice_id": default_config["voice_id"],
                "speed": 1.0
            },
            "background": {
                "type": "color",
                "value": default_config["background_color"]
                # OR use image:
                # "type": "image",
                # "url": "https://example.com/background.jpg"
            }
        }],
        "dimension": {
            "width": default_config["width"],
            "height": default_config["height"]
        },
        "aspect_ratio": default_config["aspect_ratio"]
    }
    
    # ... rest of code
```

### Platform-Specific Video Formats

```python
def _get_video_config(self, platform: str) -> Dict:
    """Get platform-specific video configuration"""
    
    configs = {
        "youtube": {
            "aspect_ratio": "16:9",
            "width": 1920,
            "height": 1080
        },
        "instagram": {
            "aspect_ratio": "9:16",  # Portrait for Reels
            "width": 1080,
            "height": 1920
        },
        "pinterest": {
            "aspect_ratio": "2:3",  # Portrait
            "width": 1000,
            "height": 1500
        },
        "twitter": {
            "aspect_ratio": "16:9",
            "width": 1280,
            "height": 720
        }
    }
    
    return configs.get(platform, configs["youtube"])
```

### Add Custom Overlays

Post-process videos with overlays:

```python
def add_overlay(self, video_path: str, product_data: Dict) -> str:
    """Add text overlay to video"""
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    
    video = VideoFileClip(video_path)
    
    # Create text overlay
    txt_clip = TextClip(
        f"{product_data['name']}\n${product_data['price']}",
        fontsize=70,
        color='white',
        font='Arial-Bold',
        bg_color='rgba(0,0,0,0.5)',
        size=(video.w, None)
    ).set_position(('center', 'bottom')).set_duration(video.duration)
    
    # Composite
    final = CompositeVideoClip([video, txt_clip])
    
    output_path = video_path.replace('.mp4', '_overlay.mp4')
    final.write_videofile(output_path)
    
    return output_path
```

### Multiple Avatars

Rotate between different avatars:

```python
def get_next_avatar(self) -> str:
    """Get next avatar in rotation"""
    avatars = [
        "avatar_1",
        "avatar_2", 
        "avatar_3"
    ]
    
    # Load current index from state
    current = self.state_manager.state.get('avatar_index', 0)
    
    # Get avatar
    avatar = avatars[current % len(avatars)]
    
    # Update index
    self.state_manager.state['avatar_index'] = current + 1
    self.state_manager.save_state()
    
    return avatar
```

---

## Platform-Specific Posting

### Customize Post Content

```python
def prepare_post_content(self, product_data: Dict, platform: str) -> Dict:
    """Prepare platform-specific post content"""
    
    content = {
        "youtube": {
            "title": f"{product_data['name']} - Full Review",
            "description": f"""
{product_data['description']}

🛒 Get it here: {product_data['link']}
💰 Price: {product_data['price']}

⏰ Timestamps:
0:00 - Introduction
0:15 - Features
0:45 - Benefits
1:15 - Call to Action

#productreview #{product_data['name'].replace(' ', '')}
            """,
            "tags": self._generate_tags(product_data),
            "category": "22"  # People & Blogs
        },
        "instagram": {
            "caption": f"""
{product_data['name']} 🔥

{product_data['description'][:150]}...

Link in bio! 🔗

#{' #'.join(self._generate_tags(product_data))}
            """[:2200]  # Instagram limit
        },
        "pinterest": {
            "title": product_data['name'][:100],
            "description": f"{product_data['description'][:400]} Pin to save!"
        },
        "twitter": {
            "text": f"""
🚀 {product_data['name']}

{product_data['description'][:150]}...

💰 {product_data['price']}
🔗 {product_data['link']}
            """[:280]  # Twitter limit
        }
    }
    
    return content[platform]

def _generate_tags(self, product_data: Dict) -> list:
    """Generate relevant hashtags"""
    tags = []
    
    # From product tags
    if 'tags' in product_data:
        tags.extend(product_data['tags'].split(','))
    
    # From product name
    tags.append(product_data['name'].replace(' ', ''))
    
    # Add general tags
    tags.extend(['product', 'review', 'shopping', 'musthave'])
    
    return [tag.strip().lower() for tag in tags[:15]]
```

### Schedule Posts at Optimal Times

```python
def get_optimal_post_time(self, platform: str) -> str:
    """Get optimal posting time for platform"""
    
    optimal_times = {
        "youtube": "14:00",  # 2 PM
        "instagram": "11:00",  # 11 AM
        "pinterest": "20:00",  # 8 PM
        "twitter": "12:00"  # Noon
    }
    
    return optimal_times.get(platform, "09:00")

def schedule_post(self, video_path: str, platform: str, content: Dict):
    """Schedule post for optimal time"""
    import schedule
    
    optimal_time = self.get_optimal_post_time(platform)
    
    schedule.every().day.at(optimal_time).do(
        self.post_to_platform,
        platform=platform,
        video_path=video_path,
        content=content
    )
```

---

## Scheduling

### Custom Schedule Patterns

```python
def setup_custom_schedule(self):
    """Set up custom scheduling patterns"""
    
    # Different products for different days
    schedule.every().monday.at("09:00").do(self.process_category, category="electronics")
    schedule.every().wednesday.at("09:00").do(self.process_category, category="fashion")
    schedule.every().friday.at("09:00").do(self.process_category, category="home")
    
    # Multiple posts per day
    for time in ["09:00", "14:00", "20:00"]:
        schedule.every().day.at(time).do(self.run_automation)
    
    # Weekend schedule
    schedule.every().saturday.at("10:00").do(self.process_featured_products)
    schedule.every().sunday.at("15:00").do(self.process_trending_products)
```

### Rate Limiting

```python
class RateLimiter:
    """Prevent hitting API rate limits"""
    
    def __init__(self):
        self.last_call = {}
        self.min_interval = {
            'youtube': 10,  # seconds
            'instagram': 60,
            'pinterest': 5,
            'twitter': 15
        }
    
    def wait_if_needed(self, platform: str):
        """Wait if rate limit requires"""
        if platform in self.last_call:
            elapsed = time.time() - self.last_call[platform]
            min_interval = self.min_interval.get(platform, 10)
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.info(f"Rate limiting {platform}: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
        
        self.last_call[platform] = time.time()
```

---

## Adding New Platforms

### TikTok Example

```python
class TikTokUploader:
    """Upload videos to TikTok"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://open-api.tiktok.com"
    
    def upload(self, video_path: str, caption: str) -> str:
        """Upload video to TikTok"""
        # Step 1: Initialize upload
        init_url = f"{self.base_url}/share/video/upload/"
        
        # Step 2: Upload video
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'access_token': self.access_token,
                'caption': caption[:2200],
                'privacy_level': 'PUBLIC_TO_EVERYONE'
            }
            
            response = requests.post(init_url, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            share_id = result['data']['share_id']
            
            logger.info(f"Uploaded to TikTok: {share_id}")
            return share_id
```

Add to main automation:

```python
# In __init__:
self.tiktok_uploader = TikTokUploader(secrets['tiktok_access_token'])

# In process_product:
try:
    logger.info("Uploading to TikTok...")
    results['tiktok'] = self.tiktok_uploader.upload(video_path, description[:2200])
except Exception as e:
    logger.error(f"TikTok upload failed: {e}")
    results['tiktok'] = f"Failed: {str(e)}"
```

---

## Advanced Features

### A/B Testing

```python
def create_ab_test(self, product_data: Dict):
    """Create A/B test versions"""
    
    # Version A: Feature-focused
    script_a = self.script_generator.generate_script(
        product_data,
        style="feature_focused"
    )
    
    # Version B: Benefit-focused
    script_b = self.script_generator.generate_script(
        product_data,
        style="benefit_focused"
    )
    
    # Create videos
    video_a = self.heygen_client.create_video(script_a, product_data)
    video_b = self.heygen_client.create_video(script_b, product_data)
    
    # Post and track
    self.post_and_track(video_a, "version_a")
    self.post_and_track(video_b, "version_b")
```

### Analytics Tracking

```python
class AnalyticsTracker:
    """Track video performance"""
    
    def __init__(self, db_path: str = "analytics.db"):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create analytics tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                product_name TEXT,
                platform TEXT,
                url TEXT,
                posted_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()
    
    def record_post(self, product_name: str, platform: str, url: str):
        """Record a new post"""
        self.conn.execute("""
            INSERT INTO videos (product_name, platform, url, posted_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (product_name, platform, url))
        self.conn.commit()
    
    def update_metrics(self, video_id: int, views: int, likes: int, comments: int, shares: int):
        """Update video metrics"""
        self.conn.execute("""
            UPDATE videos 
            SET views=?, likes=?, comments=?, shares=?
            WHERE id=?
        """, (views, likes, comments, shares, video_id))
        self.conn.commit()
```

### Thumbnail Generation

```python
def generate_thumbnail(self, video_path: str, product_data: Dict) -> str:
    """Generate custom thumbnail"""
    from PIL import Image, ImageDraw, ImageFont
    import cv2
    
    # Extract frame from video
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 3000)  # 3 seconds in
    success, frame = cap.read()
    cap.release()
    
    if not success:
        return None
    
    # Convert to PIL
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    
    # Add text overlay
    font = ImageFont.truetype("Arial.ttf", 60)
    text = product_data['name']
    
    # Add text shadow
    draw.text((52, 52), text, font=font, fill="black")
    draw.text((50, 50), text, font=font, fill="white")
    
    # Save thumbnail
    thumbnail_path = video_path.replace('.mp4', '_thumb.jpg')
    img.save(thumbnail_path, quality=95)
    
    return thumbnail_path
```

---

## Environment-Specific Configs

```python
# config.py
import os

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # Google Cloud
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    
    # Video settings
    VIDEO_QUALITY = 'high'
    MAX_VIDEO_LENGTH = 90
    
    # Posting
    POST_TO_YOUTUBE = True
    POST_TO_INSTAGRAM = True
    POST_TO_PINTEREST = True
    POST_TO_TWITTER = True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    VIDEO_QUALITY = 'medium'
    POST_TO_YOUTUBE = False  # Don't post during dev
    POST_TO_INSTAGRAM = False
    POST_TO_PINTEREST = False
    POST_TO_TWITTER = False

class ProductionConfig(Config):
    """Production configuration"""
    VIDEO_QUALITY = 'high'
    # All posting enabled

# Select config
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}[os.getenv('ENVIRONMENT', 'production')]()
```

---

Need more customization help? Check the API documentation for each service!
