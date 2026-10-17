with open('app/routers/upload.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add EXIF extraction before watermarking in upload_file
old_block = '''    file_type = "pdf" if file_ext == ".pdf" else "image"

    # 【功能 7】若為圖片且開啟浮水印，自動壓印
    is_watermarked = False
    if file_type == "image" and watermark:
        add_watermark_to_image(target_path)
        is_watermarked = True

    return {'''

new_block = '''    file_type = "pdf" if file_ext == ".pdf" else "image"

    # 【功能 49】提取相片原始 EXIF 拍攝時間與相機型號 (在壓印浮水印之前解析)
    exif_date = None
    camera_model = None
    if file_type == "image":
        try:
            from PIL import Image, ExifTags
            with Image.open(target_path) as img:
                exif = img.getexif()
                if exif:
                    for tag_id, val in exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag_name in ("DateTimeOriginal", "DateTime"):
                            exif_date = str(val)[:10].replace(":", "-")
                        elif tag_name == "Model":
                            camera_model = str(val)
        except Exception:
            pass

    # 【功能 7】若為圖片且開啟浮水印，自動壓印
    is_watermarked = False
    if file_type == "image" and watermark:
        add_watermark_to_image(target_path)
        is_watermarked = True

    return {
        "exif_date": exif_date,
        "camera_model": camera_model,'''

assert old_block in text, 'old_block not found'
text = text.replace(old_block, new_block, 1)

# Add GET /extract-exif endpoint
exif_endpoint = '''
# ==============================================================================
# 【功能 49】照片 EXIF 拍攝時間與中繼資料解析 API
# ==============================================================================
@router.get("/extract-exif")
def extract_photo_exif(filename: str):
    """【功能 49】解析已上傳照片之 EXIF 拍攝時間，用於自動校正活動日期"""
    file_path = UPLOAD_DIR / Path(filename).name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="找不到指定照片檔案")

    exif_info = {"has_exif": False, "exif_date": None, "camera_model": None}
    try:
        from PIL import Image, ExifTags
        with Image.open(file_path) as img:
            exif = img.getexif()
            if exif:
                for tag_id, val in exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag_name in ("DateTimeOriginal", "DateTime"):
                        exif_info["exif_date"] = str(val)[:10].replace(":", "-")
                        exif_info["has_exif"] = True
                    elif tag_name == "Model":
                        exif_info["camera_model"] = str(val)
    except Exception as e:
        exif_info["error"] = str(e)

    return exif_info
'''

target_sub = '# ==============================================================================\n# Canva 簡報與海報設計器 API (Canvas Slides Router)'
assert target_sub in text, 'target_sub not found'
text = text.replace(target_sub, exif_endpoint + '\n' + target_sub, 1)

with open('app/routers/upload.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('app/routers/upload.py updated with EXIF extraction!')
