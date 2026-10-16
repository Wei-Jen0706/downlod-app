import os
import time
import random
import io
import zipfile
import requests
import streamlit as st

st.set_page_config(page_title="MOPS 年報下載器", layout="wide")

st.title("📄 公開資訊觀測站 (MOPS) 年報自動下載器")

# 1. 使用者輸入
col1, col2 = st.columns(2)
with col1:
    companies_input = st.text_input("請輸入公司代號（以逗號分隔）", "2330, 2317")
with col2:
    years_input = st.text_input("請輸入民國年份（以逗號分隔）", "111, 112")

companies = [c.strip().zfill(4) for c in companies_input.split(',') if c.strip()]
years = [y.strip() for y in years_input.split(',') if y.strip()]

# 2. 觸發下載按鈕
if st.button("🚀 開始測試下載", type="primary"):
    if not companies or not years:
        st.error("請輸入有效的公司代號與年份！")
    else:
        st.info(f"準備下載公司：{companies} | 年份：{years}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8'
        }
        
        zip_buffer = io.BytesIO()
        total_tasks = len(companies) * len(years)
        current = 0
        success_count = 0
        
        # 建立狀態顯示區塊
        status_container = st.status("正在連線至公開資訊觀測站...", expanded=True)
        progress_bar = st.progress(0)

        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for year in years:
                for company in companies:
                    current += 1
                    status_container.write(f"🔍 [{current}/{total_tasks}] 正在嘗試擷取：{company} - {year} 年度...")
                    progress_bar.progress(current / total_tasks)
                    
                    possible_suffixes = ['_F04_01.pdf', '_F04.pdf', '_F04_02.pdf']
                    downloaded = False
                    
                    for suffix in possible_suffixes:
                        remote_filename = f"{company}_{year}{suffix}"
                        url = f"https://mops.twse.com.tw/doc/mops/finance/e_book/F04/{year}/{remote_filename}"
                        
                        try:
                            # 設定 8 秒連線逾時，避免雲端主機無反應
                            res = requests.get(url, headers=headers, timeout=8)
                            
                            if res.status_code == 200 and len(res.content) > 20000 and res.content.startswith(b'%PDF'):
                                save_name = f"{company}_{year}_年報.pdf"
                                zip_file.writestr(save_name, res.content)
                                status_container.write(f"✅ 成功下載：{save_name} ({round(len(res.content)/1024/1024, 2)} MB)")
                                downloaded = True
                                success_count += 1
                                break
                            elif res.status_code == 403:
                                status_container.write(f"⚠️ 被伺服器阻擋 (HTTP 403 Forbidden)：{company}_{year}")
                        except requests.exceptions.Timeout:
                            status_container.write(f"⏱️ 連線逾時 (Timeout)：{company}_{year}")
                        except Exception as e:
                            status_container.write(f"❌ 錯誤 ({company}_{year}): {str(e)}")
                    
                    if not downloaded:
                        status_container.write(f"❌ 未找到該年度年報：{company}_{year}")
                    
                    time.sleep(random.uniform(1.0, 2.0))

        if success_count > 0:
            status_container.update(label=f"🎉 處理完成！成功抓取 {success_count}/{total_tasks} 個檔案", state="complete")
            st.success("請點擊下方按鈕下載打包好的年報 ZIP 檔：")
            st.download_button(
                label="📦 下載年報 ZIP 壓縮檔",
                data=zip_buffer.getvalue(),
                file_name="MOPS_Annual_Reports.zip",
                mime="application/zip"
            )
        else:
            status_container.update(label="⚠️ 未能成功下載任何年報，請檢查 Log 或嘗試本機執行。", state="error")
            st.warning("若持續顯示 Timeout 或被拒絕，說明 MOPS 阻擋了雲端伺服器 IP，建議改在本地電腦直接執行 Python 腳本。")