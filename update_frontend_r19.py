import re

# 1. Update admin.html
with open('app/static/admin.html', 'r', encoding='utf-8') as f:
    admin_html = f.read()

# Add buttons in the sidebar navigation
nav_target = """<button @click="currentTab = 'milestonesvg'; fetchMilestoneSvg()" :class="currentTab === 'milestonesvg' ? 'bg-amber-500 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800'" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left">
              <span class="text-lg">📜</span>
              <span class="font-medium text-sm">弘法大事紀向量圖</span>
            </button>"""

r19_nav_buttons = """<button @click="currentTab = 'milestonesvg'; fetchMilestoneSvg()" :class="currentTab === 'milestonesvg' ? 'bg-amber-500 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800'" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left">
              <span class="text-lg">📜</span>
              <span class="font-medium text-sm">弘法大事紀向量圖</span>
            </button>
            <button @click="currentTab = 'customsurvey'; fetchAdminCustomSurveys()" :class="currentTab === 'customsurvey' ? 'bg-amber-500 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800'" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left">
              <span class="text-lg">📝</span>
              <span class="font-medium text-sm">問卷題目設計器</span>
            </button>
            <button @click="currentTab = 'procurement'; fetchAdminProcurement()" :class="currentTab === 'procurement' ? 'bg-amber-500 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800'" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left">
              <span class="text-lg">⚖️</span>
              <span class="font-medium text-sm">物資比價與廠商名錄</span>
            </button>
            <button @click="currentTab = 'cadrenotice'; fetchAdminCadreNotices()" :class="currentTab === 'cadrenotice' ? 'bg-amber-500 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800'" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left">
              <span class="text-lg">📢</span>
              <span class="font-medium text-sm">幹部內部公佈欄</span>
            </button>"""

if nav_target in admin_html and 'currentTab = \'customsurvey\'' not in admin_html:
    admin_html = admin_html.replace(nav_target, r19_nav_buttons)
    print("Added R19 sidebar navigation buttons in admin.html!")

# Add tab panels before </main>
main_close = "</main>"
r19_tab_panels = """
        <!-- Tab: 問卷題目自訂設計器 (功能 91) -->
        <div v-if="currentTab === 'customsurvey'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
              <div>
                <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <span>📝</span> 活動滿意度問卷自訂題目設計器 (功能 91)
                </h3>
                <p class="text-xs text-slate-500 mt-1">為指定佐證活動設計動態題目，支援單選、評分與開放式文字回饋。</p>
              </div>
              <div class="flex items-center gap-3">
                <select v-model="selectedSurveyEvidenceId" @change="fetchAdminCustomSurveys" class="text-sm border border-slate-200 rounded-lg px-3 py-2">
                  <option v-for="ev in evidenceItems" :key="ev.id" :value="ev.id">活動 #{{ ev.id }}: {{ ev.title }}</option>
                </select>
                <button @click="showAddQuestionModal = true" class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium transition flex items-center gap-1 shadow-sm">
                  <span>➕</span> 新增題目
                </button>
              </div>
            </div>

            <!-- 題目列表 -->
            <div class="mt-6 space-y-4">
              <div v-if="customQuestions.length === 0" class="text-center py-12 text-slate-400">
                此活動尚未設定自訂問卷題目，點擊上方按鈕立即建立。
              </div>
              <div v-for="(q, idx) in customQuestions" :key="q.id" class="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="w-6 h-6 rounded-full bg-amber-100 text-amber-800 text-xs font-bold flex items-center justify-center">{{ idx + 1 }}</span>
                    <span class="font-bold text-slate-800 text-sm">{{ q.question_text }}</span>
                    <span class="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">{{ q.question_type }}</span>
                    <span v-if="q.is_required" class="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">必填</span>
                  </div>
                  <div v-if="q.options_json" class="mt-2 text-xs text-slate-500 pl-8">
                    選項：{{ q.options_json }}
                  </div>
                </div>
                <button @click="deleteCustomQuestion(q.id)" class="text-red-500 hover:text-red-700 text-xs font-medium px-2 py-1 rounded bg-red-50 hover:bg-red-100 transition">
                  刪除
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 物資比價與廠商名錄 (功能 93) -->
        <div v-if="currentTab === 'procurement'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
              <div>
                <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <span>⚖️</span> 活動物資採購比價清單與特約廠商名錄 (功能 93)
                </h3>
                <p class="text-xs text-slate-500 mt-1">統籌弘法物資三方比價決策、價格透明度與常住特約良心廠商名單。</p>
              </div>
              <div class="flex gap-2">
                <button @click="showAddVendorModal = true" class="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition flex items-center gap-1">
                  <span>🏬</span> 新增廠商
                </button>
                <button @click="showAddCompModal = true" class="px-3 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-medium transition flex items-center gap-1">
                  <span>📋</span> 新增比價單
                </button>
              </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
              <!-- 特約廠商名錄 -->
              <div class="lg:col-span-1 border border-slate-200 rounded-xl p-4 bg-slate-50">
                <h4 class="font-bold text-slate-800 text-sm mb-3 flex items-center gap-1">
                  <span>🏬</span> 合作廠商名錄 ({{ adminVendors.length }})
                </h4>
                <div class="space-y-3 max-h-96 overflow-y-auto pr-1">
                  <div v-for="v in adminVendors" :key="v.id" class="bg-white p-3 rounded-lg border border-slate-200 shadow-sm text-xs">
                    <div class="flex justify-between items-start font-bold text-slate-800">
                      <span>{{ v.vendor_name }}</span>
                      <span class="text-amber-600">⭐ {{ v.rating_score }}</span>
                    </div>
                    <div class="text-slate-500 mt-1">類別：{{ v.category }} | 聯絡人：{{ v.contact_person }}</div>
                    <div class="text-slate-500">電話：{{ v.phone }}</div>
                    <div class="text-slate-400 mt-1">{{ v.notes }}</div>
                  </div>
                </div>
              </div>

              <!-- 比價清單 -->
              <div class="lg:col-span-2 space-y-4">
                <h4 class="font-bold text-slate-800 text-sm flex items-center gap-1">
                  <span>📊</span> 採購比價分析表 ({{ adminComparisons.length }})
                </h4>
                <div v-for="c in adminComparisons" :key="c.id" class="p-4 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2">
                  <div class="flex justify-between items-center">
                    <span class="font-bold text-slate-800 text-sm">{{ c.item_title }}</span>
                    <span class="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium">{{ c.category }}</span>
                  </div>
                  <div class="grid grid-cols-3 gap-2 text-xs py-2 border-y border-slate-100 text-center">
                    <div class="p-2 rounded bg-slate-50 border" :class="c.selected_vendor === c.vendor_a ? 'border-amber-400 bg-amber-50/50 font-bold' : ''">
                      <div class="text-slate-500">廠商 A: {{ c.vendor_a }}</div>
                      <div class="text-slate-800 mt-1 font-bold">NT$ {{ c.price_a }}</div>
                    </div>
                    <div class="p-2 rounded bg-slate-50 border" :class="c.selected_vendor === c.vendor_b ? 'border-amber-400 bg-amber-50/50 font-bold' : ''">
                      <div class="text-slate-500">廠商 B: {{ c.vendor_b || '無' }}</div>
                      <div class="text-slate-800 mt-1 font-bold">NT$ {{ c.price_b || '-' }}</div>
                    </div>
                    <div class="p-2 rounded bg-slate-50 border" :class="c.selected_vendor === c.vendor_c ? 'border-amber-400 bg-amber-50/50 font-bold' : ''">
                      <div class="text-slate-500">廠商 C: {{ c.vendor_c || '無' }}</div>
                      <div class="text-slate-800 mt-1 font-bold">NT$ {{ c.price_c || '-' }}</div>
                    </div>
                  </div>
                  <div class="flex justify-between text-xs text-slate-600 pt-1">
                    <div>決標廠商：<span class="font-bold text-emerald-600">{{ c.selected_vendor }}</span></div>
                    <div class="text-slate-500">決策依據：{{ c.rationale }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 幹部內部公佈欄 (功能 94) -->
        <div v-if="currentTab === 'cadrenotice'" class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
              <div>
                <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <span>📢</span> 青年幹部即時內部通知公佈欄 (功能 94)
                </h3>
                <p class="text-xs text-slate-500 mt-1">常住法師與分團幹部即時內部叮嚀、值班提醒與動員指令。</p>
              </div>
              <button @click="showAddNoticeModal = true" class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium transition flex items-center gap-1 shadow-sm">
                <span>➕</span> 發布內部通知
              </button>
            </div>

            <div class="mt-6 space-y-4">
              <div v-for="n in adminNotices" :key="n.id" class="p-4 rounded-xl border border-slate-200 bg-slate-50/40 relative">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span :class="n.priority === 'urgent' ? 'bg-red-500 text-white' : 'bg-slate-200 text-slate-700'" class="text-xs font-bold px-2 py-0.5 rounded-full uppercase">
                      {{ n.priority === 'urgent' ? '緊急重要' : '一般通知' }}
                    </span>
                    <span class="font-bold text-slate-800 text-sm">{{ n.title }}</span>
                  </div>
                  <button @click="deleteCadreNotice(n.id)" class="text-red-500 hover:text-red-700 text-xs px-2 py-1 rounded bg-red-50 hover:bg-red-100">
                    撤回
                  </button>
                </div>
                <div class="mt-2 text-xs text-slate-600 leading-relaxed whitespace-pre-line pl-1">
                  {{ n.content }}
                </div>
                <div class="mt-3 flex justify-between items-center text-xs text-slate-400 border-t border-slate-100 pt-2">
                  <div>發布人：<span class="font-medium text-slate-600">{{ n.publisher_name }}</span> | 對象：<span class="text-amber-600 font-medium">{{ n.target_roles }}</span></div>
                  <div>{{ n.created_at }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
</main>"""

if main_close in admin_html and 'currentTab === \'customsurvey\'' not in admin_html:
    admin_html = admin_html.replace(main_close, r19_tab_panels)
    print("Added R19 tab panels in admin.html!")

# Add JS functions in admin.html
js_target = "const fetchAdminTeaBookings = async () => {"
r19_js_methods = """
    // Round 19 Functions
    const selectedSurveyEvidenceId = ref(1);
    const customQuestions = ref([]);
    const adminVendors = ref([]);
    const adminComparisons = ref([]);
    const adminNotices = ref([]);
    const showAddQuestionModal = ref(false);
    const showAddVendorModal = ref(false);
    const showAddCompModal = ref(false);
    const showAddNoticeModal = ref(false);

    const fetchAdminCustomSurveys = async () => {
      try {
        const res = await axios.get(`/api/custom-surveys/${selectedSurveyEvidenceId.value}`);
        customQuestions.value = res.data;
      } catch (err) {
        console.error(err);
      }
    };

    const deleteCustomQuestion = async (id) => {
      if (!confirm('確定刪除此題目？')) return;
      try {
        await axios.delete(`/api/custom-surveys/${id}`, {
          headers: { Authorization: `Bearer ${token.value}` }
        });
        await fetchAdminCustomSurveys();
      } catch (err) {
        alert('刪除失敗');
      }
    };

    const fetchAdminProcurement = async () => {
      try {
        const [resV, resC] = await Promise.all([
          axios.get('/api/procurement/vendors'),
          axios.get('/api/procurement/comparisons')
        ]);
        adminVendors.value = resV.data;
        adminComparisons.value = resC.data;
      } catch (err) {
        console.error(err);
      }
    };

    const fetchAdminCadreNotices = async () => {
      try {
        const res = await axios.get('/api/team/cadre-notices', {
          headers: { Authorization: `Bearer ${token.value}` }
        });
        adminNotices.value = res.data;
      } catch (err) {
        console.error(err);
      }
    };

    const deleteCadreNotice = async (id) => {
      if (!confirm('確定撤回此通知？')) return;
      try {
        await axios.delete(`/api/team/cadre-notices/${id}`, {
          headers: { Authorization: `Bearer ${token.value}` }
        });
        await fetchAdminCadreNotices();
      } catch (err) {
        alert('撤回失敗');
      }
    };

    const fetchAdminTeaBookings = async () => {"""

if js_target in admin_html and 'fetchAdminCustomSurveys' not in admin_html:
    admin_html = admin_html.replace(js_target, r19_js_methods)
    print("Added R19 JS methods in admin.html!")

# Add to return statement of setup()
return_target = "fetchAdminTeaBookings,"
r19_returns = """fetchAdminTeaBookings,
      selectedSurveyEvidenceId, customQuestions, adminVendors, adminComparisons, adminNotices,
      showAddQuestionModal, showAddVendorModal, showAddCompModal, showAddNoticeModal,
      fetchAdminCustomSurveys, deleteCustomQuestion, fetchAdminProcurement, fetchAdminCadreNotices, deleteCadreNotice,"""

if return_target in admin_html and 'fetchAdminCustomSurveys,' not in admin_html:
    admin_html = admin_html.replace(return_target, r19_returns)
    print("Added R19 returns in admin.html!")

with open('app/static/admin.html', 'w', encoding='utf-8') as f:
    f.write(admin_html)

print("admin.html update complete!")
