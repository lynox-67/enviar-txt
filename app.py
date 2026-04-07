from flask import Flask, request, jsonify
import re
import asyncio
import os
from TikTokApi import TikTokApi

app = Flask(__name__)

def extraer_links(texto):
    if not texto:
        return []
    return re.findall(r'https?://[^\s<>"]+', texto)

async def obtener_links_de_video(api, video_url):
    links = set()
    try:
        video = await api.video(url=video_url)
        async for comment in video.comments(count=150):
            texto = str(comment.as_dict.get('text', ''))
            for link in extraer_links(texto):
                links.add(link)
    except Exception as e:
        print(f"Error en vídeo: {e}")
    return links

async def obtener_links_de_busqueda(api, keywords, max_videos=20):
    all_links = set()
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
    
    try:
        for kw in keyword_list:
            count = 0
            async for video in api.search.videos(kw, count=max_videos):
                if count >= max_videos:
                    break
                video_url = f"https://www.tiktok.com/video/{video.as_dict.get('id')}"
                links = await obtener_links_de_video(api, video_url)
                all_links.update(links)
                count += 1
                await asyncio.sleep(1.2)  # Evita bloqueos
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    
    return all_links

@app.route('/extraer', methods=['POST'])
def extraer():
    data = request.get_json()
    mode = data.get('mode')
    
    ms_token = os.environ.get("MS_TOKEN", None)
    
    try:
        async def main():
            async with TikTokApi() as api:
                await api.create_sessions(
                    ms_tokens=[ms_token] if ms_token else [],
                    num_sessions=1,
                    sleep_after=3,
                    browser="chromium"
                )
                
                if mode == 'single':
                    url = data.get('url')
                    links = await obtener_links_de_video(api, url)
                elif mode == 'search':
                    keywords = data.get('keywords', '')
                    max_videos = data.get('maxVideos', 20)
                    links = await obtener_links_de_busqueda(api, keywords, max_videos)
                else:
                    links = set()
                
                return sorted(list(links))
        
        links = asyncio.run(main())
        
        return jsonify({
            'links': links,
            'total_links': len(links)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    try:
        with open('index.html', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: No se encontró index.html</h1>", 404

if __name__ == '__main__':
    print("🚀 SHADOW LINK corriendo → http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
