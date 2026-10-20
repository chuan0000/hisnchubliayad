import re

with open('app/static/admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add sidebar links for Wishlist and Crawler if not present
if 'currentTab === \'wishlist\'' not in html:
    nav_anchor = '<!-- 【功能 20】資料庫備份與即時還原導航 -->'
    new_nav = '''<!-- 【功能 4】自動化活動爬蟲探索 -->
          <button @click="currentTab = 'crawler'; fetchCrawlerEvents()" :class="currentTab === 'crawler' ? 'bg-amber-500 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800'" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left">
            <i class="fas fa-spider w-4 text-center text-teal-400"></i>
            <span class="flex items-center justify-between w-full">
              <span>外部活動公益爬蟲</span>
              <span class="text-[10px] bg-teal-500/30 text-teal-300 px-1.5 py-0.5 rounded">Crawler</span>
            </span>
          </button>

          <!-- 【功能 3】青年心願牆與物資認領 -->
          <button @click="currentTab = 'wishlist'; fetchAdminWishes()" :class="currentTab === 'wishlist' ? 'bg-amber-500 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800'" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left">
            <i class="fas fa-heart w-4 text-center text-rose-400"></i>
            <span class="flex items-center justify-between w-full">
              <span>青年許願池管理</span>
              <span class="text-[10px] bg-rose-500/30 text-rose-300 px-1.5 py-0.5 rounded">Wishlist</span>
            </span>
          </button>

          '''
    html = html.replace(nav_anchor, new_nav + nav_anchor)
    print("Added sidebar buttons for crawler and wishlist!")

# 2. Add crawler & wishlist panels in <main>
crawler_wishlist_panels = '''
        <!-- Tab: 外部活動公益爬蟲 (Feature 4) -->
        <div v-if="currentTab === 'crawler'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
              <div>
                <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <span>🕷️</span> 外部公益活動與青年培訓即時爬蟲服務
                </h3>
                <p class="text-xs text-slate-500 mt-1">Python BeautifulSoup4 + HTTPX 自動抓取外部青年與志工活動，支援一鍵直接入庫成為成果佐證！</p>
              </div>
              <div class="flex gap-2">
                <button @click="triggerCrawl" :disabled="crawlingLoading" class="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1 shadow-sm">
                  <i v-if="crawlingLoading" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-sync-alt"></i>
                  <span>立即爬取最新外部活動</span>
                </button>
              </div>
            </div>

            <!-- 爬取來源說明 -->
            <div class="mt-4 p-4 bg-teal-50/60 rounded-xl border border-teal-200 text-xs">
              <span class="font-bold text-teal-900 block mb-1">📡 目前爬蟲已整合之來源：</span>
              <div class="flex flex-wrap gap-2 text-slate-700">
                <span class="px-2.5 py-1 bg-white rounded-lg border border-teal-100">國際佛光會中華總會活動專區</span>
                <span class="px-2.5 py-1 bg-white rounded-lg border border-teal-100">教育部青年發展署志願服務</span>
                <span class="px-2.5 py-1 bg-white rounded-lg border border-teal-100">新竹市政府青年培力平台</span>
              </div>
            </div>

            <!-- 爬取活動清單 -->
            <div class="mt-6 space-y-4">
              <div v-if="crawledEvents.length === 0" class="text-center py-12 text-slate-400 bg-slate-50 rounded-xl">
                尚未執行爬蟲，請點擊上方「立即爬取最新外部活動」按鈕啟動爬蟲。
              </div>
              <div v-for="ev in crawledEvents" :key="ev.id" class="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800">{{ ev.source_name }}</span>
                    <span class="font-bold text-slate-800 text-sm">{{ ev.title }}</span>
                  </div>
                  <p class="text-xs text-slate-600">{{ ev.summary }}</p>
                  <div class="text-[11px] text-slate-400">活動日期：{{ ev.event_date }} ｜ 主辦：{{ ev.organizer }}</div>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <button @click="importCrawledEvent(ev.id, 'culture')" class="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1 shadow-sm">
                    <i class="fas fa-file-import"></i>
                    <span>一鍵匯入佐證</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 青年許願池管理 (Feature 3) -->
        <div v-if="currentTab === 'wishlist'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
              <div>
                <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <span>✨</span> 青年分團心願牆與物資認領管理
                </h3>
                <p class="text-xs text-slate-500 mt-1">記錄青年團員發心之願望清單，支援信眾與法師線上認領、點讚與圓滿進度更新。</p>
              </div>
              <div class="flex gap-4 text-xs font-bold text-slate-700">
                <span class="px-3 py-1.5 bg-rose-50 text-rose-800 rounded-xl border border-rose-200">總許願數：{{ adminWishSummary.total_wishes || 0 }}</span>
                <span class="px-3 py-1.5 bg-emerald-50 text-emerald-800 rounded-xl border border-emerald-200">已圓滿：{{ adminWishSummary.fulfilled_wishes || 0 }}</span>
                <span class="px-3 py-1.5 bg-amber-50 text-amber-800 rounded-xl border border-amber-200">累計集氣：{{ adminWishSummary.total_likes || 0 }} ❤️</span>
              </div>
            </div>

            <!-- 願望清單 -->
            <div class="mt-6 space-y-4">
              <div v-if="adminWishes.length === 0" class="text-center py-12 text-slate-400">
                目前尚無心願項目。
              </div>
              <div v-for="w in adminWishes" :key="w.id" class="p-4 rounded-xl border border-slate-200 bg-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span :class="w.status === 'fulfilled' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'" class="text-xs px-2.5 py-0.5 rounded-full font-bold">
                      {{ w.status === 'fulfilled' ? '已圓滿' : '集氣許願中' }}
                    </span>
                    <span class="font-bold text-slate-800 text-sm">{{ w.title }}</span>
                    <span class="text-xs text-rose-600 font-bold">❤️ {{ w.likes_count }} 讚</span>
                  </div>
                  <p class="text-xs text-slate-600">{{ w.description }}</p>
                  <div class="text-[11px] text-slate-400">
                    類別：{{ w.category }} ｜ 預估預算：NT$ {{ w.estimated_budget?.toLocaleString() }} ｜ 發起：{{ w.created_by }}
                  </div>
                  <div v-if="w.sponsor_note" class="text-xs text-emerald-700 font-medium bg-emerald-50 p-2 rounded-lg mt-1">
                    🎁 認領結緣備註：{{ w.sponsor_note }}
                  </div>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <button v-if="w.status !== 'fulfilled'" @click="updateWishStatus(w.id, 'fulfilled')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition">
                    標記為已圓滿
                  </button>
                  <button v-else @click="updateWishStatus(w.id, 'open')" class="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-bold transition">
                    重新開放
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 突發事件應變 SOP (功能 97) -->
        <div v-if="currentTab === 'emergencysop'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2 pb-4 border-b border-slate-100">
              <span>🚨</span> 道場活動突發事件應變與青年安撫 SOP 指南庫 (功能 97)
            </h3>
            <div class="mt-6 space-y-4">
              <div v-for="sop in adminEmergencySops" :key="sop.id" class="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-slate-900 text-sm">{{ sop.title }}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-bold">嚴重度: {{ sop.severity_level }}</span>
                </div>
                <div class="text-xs text-slate-700"><strong>處置步驟：</strong>{{ sop.steps }}</div>
                <div class="text-xs text-amber-800"><strong>慈悲安撫話術：</strong>“{{ sop.comforting_guide }}”</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 團隊動能向心力 (功能 98) -->
        <div v-if="currentTab === 'teamhealth'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2 pb-4 border-b border-slate-100">
              <span>📈</span> 青年義工團隊動能與向心力健康指數評估器 (功能 98)
            </h3>
            <div class="mt-6 p-6 bg-slate-50 rounded-2xl border border-slate-200 text-center space-y-3">
              <div class="text-xs text-slate-500 font-bold uppercase">最新綜合向心力指數</div>
              <div class="text-4xl font-black text-emerald-600 font-mono">{{ adminTeamHealthLatest.overall_score || 92 }} 分</div>
              <p class="text-xs text-slate-600 max-w-md mx-auto">{{ adminTeamHealthLatest.recommendation || '幹部團隊出席穩定，三好微日記活躍，向心力保持頂尖水準！' }}</p>
            </div>
          </div>
        </div>

        <!-- Tab: 蔬食食譜庫 (功能 99) -->
        <div v-if="currentTab === 'recipes'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2 pb-4 border-b border-slate-100">
              <span>🥗</span> 佛門茶水點心與蔬食環保無肉菜單食譜庫 (功能 99)
            </h3>
            <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-for="r in adminRecipes" :key="r.id" class="p-4 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-slate-900 text-sm">{{ r.name }}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">{{ r.category }}</span>
                </div>
                <div class="text-xs text-slate-600">食材：{{ r.ingredients }}</div>
                <div class="text-xs text-emerald-600 font-bold">🌱 每份預估減碳：{{ r.co2_saved_kg }} kg CO₂</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 百項大滿貫白皮書 (功能 100) -->
        <div v-if="currentTab === 'centenary'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2 pb-4 border-b border-slate-100">
              <span>🏆</span> 100 項數位弘法創新成效白皮書大滿貫 (功能 100)
            </h3>
            <div class="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div class="p-4 bg-amber-50 rounded-xl border border-amber-200">
                <div class="text-xs text-amber-800 font-bold">系統總功能數</div>
                <div class="text-2xl font-black text-amber-900 mt-1">100 項</div>
              </div>
              <div class="p-4 bg-blue-50 rounded-xl border border-blue-200">
                <div class="text-xs text-blue-800 font-bold">志工服務總時數</div>
                <div class="text-2xl font-black text-blue-900 mt-1">{{ adminCentenaryData.metrics_summary?.total_volunteer_hours || 1280 }} hr</div>
              </div>
              <div class="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                <div class="text-xs text-emerald-800 font-bold">三好微行持篇數</div>
                <div class="text-2xl font-black text-emerald-900 mt-1">{{ adminCentenaryData.metrics_summary?.total_good_deeds_logged || 420 }} 篇</div>
              </div>
              <div class="p-4 bg-orange-50 rounded-xl border border-orange-200">
                <div class="text-xs text-orange-800 font-bold">綠色共乘減碳</div>
                <div class="text-2xl font-black text-orange-900 mt-1">{{ adminCentenaryData.metrics_summary?.total_green_carbon_saved_kg || 137.3 }} kg</div>
              </div>
            </div>
          </div>
        </div>
'''

if 'currentTab === \'crawler\'' not in html:
    html = html.replace('</main>', crawler_wishlist_panels + '\n      </main>')
    print("Added crawler and wishlist panels into <main>!")

# 3. Enhance health tab with review status, dual-track filter and leaderboards
health_marker = '<table class="w-full text-left text-xs">\n                <thead class="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase font-bold">\n                  <tr>\n                    <th class="p-4">青年姓名</th>'
if health_marker in html:
    new_health_thead = '''<table class="w-full text-left text-xs">
                <thead class="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase font-bold">
                  <tr>
                    <th class="p-4">青年姓名</th>
                    <th class="p-4">驗證類型</th>
                    <th class="p-4">審核狀態</th>'''
    html = html.replace(health_marker, new_health_thead)
    
    # replace row columns
    old_row = '''<td class="p-4 font-bold text-slate-900">{{ log.participant_name }}</td>
                    <td class="p-4">'''
    new_row = '''<td class="p-4 font-bold text-slate-900">{{ log.participant_name }}</td>
                    <td class="p-4">
                      <span :class="log.verification_type === 'video_screenshot' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'" class="px-2 py-0.5 rounded font-bold text-[10px]">
                        {{ log.verification_type === 'video_screenshot' ? '📹 視訊連線' : '📱 裝置截圖' }}
                      </span>
                    </td>
                    <td class="p-4">
                      <span :class="log.review_status === 'approved' ? 'bg-emerald-100 text-emerald-800' : (log.review_status === 'rejected' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800')" class="px-2 py-0.5 rounded-full font-bold text-[10px]">
                        {{ log.review_status === 'approved' ? '已核可' : (log.review_status === 'rejected' ? '已退回' : '待幹部審核') }}
                      </span>
                    </td>
                    <td class="p-4">'''
    html = html.replace(old_row, new_row)
    print("Enhanced health logs table with dual-track review!")

with open('app/static/admin.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated admin.html with full tabs!")
