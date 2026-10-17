with open('app/static/index.html', 'r', encoding='utf-8') as f:
    idx_html = f.read()

# 1. Add Liturgy Button next to Social Card button in #good-deeds
old_social_btn = """<span>【功能 77】產製名片級三好祈願社群分享圖卡 (SVG)</span>
          </button>"""

new_liturgy_btn = """<span>【功能 77】產製名片級三好祈願社群分享圖卡 (SVG)</span>
          </button>
          <button @click="openLiturgyModal" class="px-4 py-2 rounded-2xl bg-gradient-to-r from-amber-700 to-amber-900 text-amber-100 font-bold text-xs shadow-md hover:shadow-lg transition flex items-center space-x-1.5 ml-2">
            <i class="fas fa-scroll"></i>
            <span>【功能 92】功德回向文疏列印</span>
          </button>"""

if old_social_btn in idx_html and 'openLiturgyModal' not in idx_html:
    idx_html = idx_html.replace(old_social_btn, new_liturgy_btn, 1)
    print("Added Liturgy button in index.html!")

# 2. Add Calendar Sync Button in navbar
old_cal_btn = """<!-- 【功能 28】活動行事曆 iCal 訂閱按鈕 -->"""
new_cal_btn = """<!-- 【功能 95】活動行事曆 WebCal / Google Calendar 一鍵即時同步 -->
          <button @click="openCalendarSyncModal" class="text-xs px-2.5 sm:px-3 py-2 rounded-xl bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 font-bold transition flex items-center space-x-1" title="行事曆即時訂閱與同步">
            <i class="fas fa-calendar-check text-indigo-600"></i>
            <span class="hidden lg:inline">行事曆即時同步</span>
          </button>

          <!-- 【功能 28】活動行事曆 iCal 訂閱按鈕 -->"""

if old_cal_btn in idx_html and 'openCalendarSyncModal' not in idx_html:
    idx_html = idx_html.replace(old_cal_btn, new_cal_btn, 1)
    print("Added Calendar sync button in navbar!")

# 3. Add Modals before </body>
body_close = "</body>"
r19_modals = """
    <!-- 【功能 92】三好功德回向文疏 Modal -->
    <div v-if="showLiturgyModal" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-amber-50 rounded-3xl max-w-2xl w-full border border-amber-200 shadow-2xl p-6 relative">
        <button @click="showLiturgyModal = false" class="absolute top-5 right-5 text-slate-400 hover:text-slate-600 text-lg">✕</button>
        <div class="flex items-center space-x-2 text-amber-800 font-bold mb-4">
          <i class="fas fa-scroll text-xl"></i>
          <h3 class="text-lg">三好微行持功德回向文疏 (高畫質直排列印排版)</h3>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4 text-xs">
          <div>
            <label class="block text-slate-600 font-medium mb-1">發願青年姓名：</label>
            <input v-model="liturgyDonorName" type="text" class="w-full border border-amber-300 rounded-lg p-2 bg-white" placeholder="如：陳冠宇">
          </div>
          <div>
            <label class="block text-slate-600 font-medium mb-1">功德回向對象：</label>
            <input v-model="liturgyTarget" type="text" class="w-full border border-amber-300 rounded-lg p-2 bg-white" placeholder="如：新竹鄉親與闔家眷屬">
          </div>
          <div class="sm:col-span-2">
            <label class="block text-slate-600 font-medium mb-1">自訂回向祈願語：</label>
            <input v-model="liturgyPrayer" type="text" class="w-full border border-amber-300 rounded-lg p-2 bg-white" placeholder="如：願以此善行功德，祈願十方眾生身心自在、福慧日增！">
          </div>
        </div>

        <div class="flex justify-end gap-2 mb-4">
          <button @click="fetchLiturgySlip" class="px-4 py-2 bg-amber-700 hover:bg-amber-800 text-white rounded-xl text-xs font-bold transition">
            即時生成文疏
          </button>
          <button @click="printLiturgy" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition">
            🖨️ 友善列印文疏
          </button>
        </div>

        <div id="liturgy-print-area" class="border border-amber-300 rounded-2xl bg-white p-2 shadow-inner overflow-hidden max-h-[500px] flex justify-center">
          <div v-html="liturgySvg" class="w-full h-full flex justify-center"></div>
        </div>
      </div>
    </div>

    <!-- 【功能 95】行事曆即時同步引導 Modal -->
    <div v-if="showCalendarSyncModal" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-3xl max-w-lg w-full border border-slate-100 shadow-2xl p-6 relative">
        <button @click="showCalendarSyncModal = false" class="absolute top-5 right-5 text-slate-400 hover:text-slate-600 text-lg">✕</button>
        <div class="flex items-center space-x-2 text-indigo-700 font-bold mb-4">
          <i class="fas fa-calendar-alt text-xl"></i>
          <h3 class="text-lg">佛光青年年度行事曆即時同步 (WebCal)</h3>
        </div>

        <p class="text-xs text-slate-600 mb-4 leading-relaxed">
          透過 RFC 5545 國際標準 WebCal 訂閱流，將青年分團活動、共修、營隊日程自動同步到您的手機行事曆，道場時間異動時將即時更新！
        </p>

        <div class="space-y-3 text-xs mb-6">
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span class="font-bold text-slate-700 block mb-1">🔗 WebCal 即時訂閱網址：</span>
            <input readonly :value="calendarSyncData.webcal_url || 'webcal://' + window.location.host + '/api/evidence/calendar/webcal-feed'" class="w-full bg-white border border-slate-200 rounded p-1.5 text-slate-500 font-mono text-[11px] select-all">
          </div>
          <div class="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900">
            <span class="font-bold block mb-1">📱 Apple iPhone / iPad / Mac 同步方式：</span>
            點擊下方「一鍵加入 Apple 行事曆」按鈕，系統將自動開啟日曆並提示訂閱。
          </div>
          <div class="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-900">
            <span class="font-bold block mb-1">📅 Google 日曆同步方式：</span>
            {{ calendarSyncData.google_cal_import_guide || '進入 Google 日曆 -> 其他日曆 -> 透過網址新增 -> 貼上訂閱網址即可。' }}
          </div>
        </div>

        <div class="flex gap-2">
          <a :href="calendarSyncData.webcal_url || '/api/evidence/calendar/webcal-feed'" class="flex-1 text-center py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition">
            一鍵加入 Apple / 手機日曆
          </a>
          <a href="/api/evidence/calendar.ics" download class="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition">
            下載 .ICS 檔
          </a>
        </div>
      </div>
    </div>
</body>"""

if body_close in idx_html and 'showLiturgyModal' not in idx_html:
    idx_html = idx_html.replace(body_close, r19_modals)
    print("Added R19 Modals in index.html!")

# 4. Add methods in Vue setup
js_insert_target = "const fetchPassbook = async () => {"
r19_idx_js = """
    // Round 19 Features
    const showLiturgyModal = ref(false);
    const liturgyDonorName = ref('陳冠宇');
    const liturgyTarget = ref('闔家眷屬與法界眾生');
    const liturgyPrayer = ref('願以此三好微行持功德，回向十方眾生身心自在、福慧如海！');
    const liturgySvg = ref('');

    const openLiturgyModal = async () => {
      showLiturgyModal.value = true;
      await fetchLiturgySlip();
    };

    const fetchLiturgySlip = async () => {
      try {
        const res = await axios.get('/api/liturgy/print-slip', {
          params: {
            donor_name: liturgyDonorName.value,
            target: liturgyTarget.value,
            prayer_text: liturgyPrayer.value
          }
        });
        liturgySvg.value = res.data.svg_markup;
      } catch (err) {
        console.error(err);
      }
    };

    const printLiturgy = () => {
      const printWin = window.open('', '_blank');
      printWin.document.write(`
        <html>
          <head><title>三好微行持功德回向文疏</title></head>
          <body style="margin:0; padding:20px; display:flex; justify-content:center;">
            ${liturgySvg.value}
            <script>window.onload = function() { window.print(); }<\\/script>
          </body>
        </html>
      `);
      printWin.document.close();
    };

    const showCalendarSyncModal = ref(false);
    const calendarSyncData = ref({});

    const openCalendarSyncModal = async () => {
      showCalendarSyncModal.value = true;
      try {
        const res = await axios.get('/api/evidence/calendar/sync-guide');
        calendarSyncData.value = res.data;
      } catch (err) {
        console.error(err);
      }
    };

    const fetchPassbook = async () => {"""

if js_insert_target in idx_html and 'openLiturgyModal' not in idx_html:
    idx_html = idx_html.replace(js_insert_target, r19_idx_js)
    print("Added R19 Vue methods in index.html!")

# 5. Add returns in Vue setup
return_target = "fetchPassbook,"
r19_idx_returns = """fetchPassbook,
      showLiturgyModal, liturgyDonorName, liturgyTarget, liturgyPrayer, liturgySvg, openLiturgyModal, fetchLiturgySlip, printLiturgy,
      showCalendarSyncModal, calendarSyncData, openCalendarSyncModal,"""

if return_target in idx_html and 'openLiturgyModal,' not in idx_html:
    idx_html = idx_html.replace(return_target, r19_idx_returns)
    print("Added R19 returns in index.html!")

with open('app/static/index.html', 'w', encoding='utf-8') as f:
    f.write(idx_html)

print("index.html update complete!")
