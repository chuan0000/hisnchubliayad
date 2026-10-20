import re

with open('app/static/admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ensure login section has high z-index
content = content.replace(
    '<!-- 未登入畫面 -->\n    <div v-if="!isLoggedIn" class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-slate-800 to-amber-950">',
    '<!-- 未登入畫面 -->\n    <div v-if="!isLoggedIn" class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-slate-800 to-amber-950 relative z-50">'
)

# 2. Fix getAuthHeaders
pattern_getauth = r'const getAuthHeaders = \(\) => \{\s*return \{.*?\'Authorization\': `Bearer \$\{token\.value\}`,.*?\'Content-Type\': \'application/json\'\s*\};\s*\};'

fixed_getauth = '''const getAuthHeaders = () => {
          return {
            'Authorization': `Bearer ${token.value}`,
            'Content-Type': 'application/json'
          };
        };

        const authFetch = (url, options = {}) => {
          const headers = Object.assign({}, options.headers || {}, getAuthHeaders());
          return fetch(url, Object.assign({}, options, { headers }));
        };'''

if re.search(pattern_getauth, content, re.DOTALL):
    content = re.sub(pattern_getauth, fixed_getauth, content, count=1, flags=re.DOTALL)
    print("Replaced getAuthHeaders successfully!")
else:
    print("Pattern for getAuthHeaders not matched, attempting direct replacement...")
    # Find exact boundary
    start_idx = content.find('const getAuthHeaders = () => {')
    end_idx = content.find('const handleLogin = async () => {')
    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + fixed_getauth + '\n\n        ' + content[end_idx:]
        print("Direct slice replacement for getAuthHeaders succeeded!")

# 3. Add missing state & functions before return statement
features_js = '''
        // ==============================================================================
        // 【功能 91】滿意度問卷自訂題目設計器
        // ==============================================================================
        const selectedSurveyEvidenceId = ref(1);
        const evidenceItems = computed(() => evidenceList.value);
        const customQuestions = ref([]);
        const showAddQuestionModal = ref(false);

        const fetchAdminCustomSurveys = async () => {
          if (!selectedSurveyEvidenceId.value) return;
          try {
            const res = await fetch('/api/custom-surveys/' + selectedSurveyEvidenceId.value);
            if (res.ok) customQuestions.value = await res.json();
          } catch(e) { console.error(e); }
        };

        const deleteCustomQuestion = async (id) => {
          if (!confirm('確定刪除此問卷題目？')) return;
          try {
            const res = await authFetch('/api/custom-surveys/' + id, { method: 'DELETE' });
            if (res.ok) fetchAdminCustomSurveys();
          } catch(e) { alert('刪除失敗'); }
        };

        // ==============================================================================
        // 【功能 93】物資採購比價與廠商名錄
        // ==============================================================================
        const adminVendors = ref([]);
        const adminComparisons = ref([]);
        const showAddVendorModal = ref(false);
        const showAddCompModal = ref(false);

        const fetchAdminProcurement = async () => {
          try {
            const [r1, r2] = await Promise.all([
              fetch('/api/procurement/vendors'),
              fetch('/api/procurement/comparisons')
            ]);
            if (r1.ok) adminVendors.value = await r1.json();
            if (r2.ok) adminComparisons.value = await r2.json();
          } catch(e) { console.error(e); }
        };

        // ==============================================================================
        // 【功能 94】幹部內部通知公佈欄
        // ==============================================================================
        const adminNotices = ref([]);
        const showAddNoticeModal = ref(false);

        const fetchAdminCadreNotices = async () => {
          try {
            const res = await authFetch('/api/team/cadre-notices');
            if (res.ok) adminNotices.value = await res.json();
          } catch(e) { console.error(e); }
        };

        const deleteCadreNotice = async (id) => {
          if (!confirm('確定撤回此通知？')) return;
          try {
            const res = await authFetch('/api/team/cadre-notices/' + id, { method: 'DELETE' });
            if (res.ok) fetchAdminCadreNotices();
          } catch(e) { alert('撤回失敗'); }
        };

        // ==============================================================================
        // 【功能 97】突發事件應變 SOP
        // ==============================================================================
        const adminEmergencySops = ref([]);
        const fetchAdminEmergencySops = async () => {
          try {
            const res = await fetch('/api/emergency-sops');
            if (res.ok) adminEmergencySops.value = await res.json();
          } catch(e) { console.error(e); }
        };

        // ==============================================================================
        // 【功能 98】團隊動能向心力
        // ==============================================================================
        const adminTeamHealthLatest = ref({});
        const fetchAdminTeamHealth = async () => {
          try {
            const res = await fetch('/api/team/dynamics-health/latest');
            if (res.ok) adminTeamHealthLatest.value = await res.json();
          } catch(e) { console.error(e); }
        };

        // ==============================================================================
        // 【功能 99】蔬食食譜與減碳
        // ==============================================================================
        const adminRecipes = ref([]);
        const adminRecipeStats = ref({});
        const fetchAdminRecipes = async () => {
          try {
            const [r1, r2] = await Promise.all([
              fetch('/api/vegetarian-recipes'),
              fetch('/api/vegetarian-recipes/stats')
            ]);
            if (r1.ok) adminRecipes.value = await r1.json();
            if (r2.ok) adminRecipeStats.value = await r2.json();
          } catch(e) { console.error(e); }
        };

        // ==============================================================================
        // 【功能 100】百項大滿貫白皮書
        // ==============================================================================
        const adminCentenaryData = ref({});
        const adminWhitepaper = ref({});
        const fetchAdminCentenary = async () => {
          try {
            const [r1, r2] = await Promise.all([
              fetch('/api/centenary/panorama-dashboard'),
              fetch('/api/centenary/whitepaper')
            ]);
            if (r1.ok) adminCentenaryData.value = await r1.json();
            if (r2.ok) {
              const d = await r2.json();
              adminWhitepaper.value = d.whitepaper;
            }
          } catch(e) { console.error(e); }
        };

        // ==============================================================================
        // 【test2 四大進階模組】健走雙軌審核、連續打卡王者榜、許願牆、活動爬蟲
        // ==============================================================================
        const pendingHealthLogs = ref([]);
        const healthLeaderboards = ref({ streak_leaderboard: [], distance_leaderboard: [] });
        const fetchHealthReviews = async () => {
          try {
            const [r1, r2] = await Promise.all([
              fetch('/api/health/pending'),
              fetch('/api/health/leaderboards')
            ]);
            if (r1.ok) pendingHealthLogs.value = await r1.json();
            if (r2.ok) healthLeaderboards.value = await r2.json();
          } catch(e) {}
        };

        const reviewHealthLog = async (logId, status) => {
          const note = prompt(`請輸入審核備註 (${status === 'approved' ? '通過' : '退回'})：`, status === 'approved' ? '核實無誤，讚歎三好精神！' : '截圖未能清楚辨識，請補件');
          if (note === null) return;
          try {
            const res = await authFetch(`/api/health/${logId}/review`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ review_status: status, reviewer_name: user.value.full_name || '幹部', reviewer_notes: note })
            });
            if (res.ok) {
              alert(status === 'approved' ? '✅ 審核已通過！' : '❌ 已標記退回！');
              loadHealth();
              fetchHealthReviews();
            }
          } catch(e) { alert('審核操作失敗'); }
        };

        const adminWishes = ref([]);
        const adminWishSummary = ref({});
        const fetchAdminWishes = async () => {
          try {
            const [r1, r2] = await Promise.all([
              fetch('/api/wishlist'),
              fetch('/api/wishlist/summary')
            ]);
            if (r1.ok) adminWishes.value = await r1.json();
            if (r2.ok) adminWishSummary.value = await r2.json();
          } catch(e) {}
        };

        const updateWishStatus = async (wishId, newStatus) => {
          const note = prompt('請填寫認領/圓滿備註：', '感謝常住法師與十方大眾慈悲護持！');
          if (note === null) return;
          try {
            const res = await authFetch(`/api/wishlist/${wishId}/status`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ status: newStatus, sponsor_note: note })
            });
            if (res.ok) {
              alert('願望狀態已更新！');
              fetchAdminWishes();
            }
          } catch(e) { alert('更新失敗'); }
        };

        const crawledEvents = ref([]);
        const crawlerSources = ref([]);
        const crawlingLoading = ref(false);
        const fetchCrawlerEvents = async () => {
          try {
            const res = await fetch('/api/crawler/sources');
            if (res.ok) crawlerSources.value = (await res.json()).sources || [];
          } catch(e) {}
        };

        const triggerCrawl = async () => {
          crawlingLoading.value = true;
          try {
            const res = await fetch('/api/crawler/fetch-external-events', { method: 'POST' });
            if (res.ok) {
              crawledEvents.value = await res.json();
              alert(`🎉 爬蟲抓取完成！成功檢索到 ${crawledEvents.value.length} 則外部公益活動！`);
            }
          } catch(e) { alert('爬蟲抓取失敗'); }
          finally { crawlingLoading.value = false; }
        };

        const importCrawledEvent = async (eventId, category = 'culture') => {
          try {
            const res = await authFetch(`/api/crawler/events/${eventId}/import-to-evidence?category=${category}`, { method: 'POST' });
            if (res.ok) {
              const d = await res.json();
              alert(`✅ 成功匯入佐證庫！佐證 ID #${d.evidence_id}`);
              loadEvidence();
            }
          } catch(e) { alert('匯入佐證失敗'); }
        };
'''

# Insert features_js right before `return {`
ret_idx = content.rfind('return {')
if ret_idx != -1:
    content = content[:ret_idx] + features_js + '\n        return {\n' + '''          evidenceItems,
          selectedSurveyEvidenceId,
          customQuestions,
          adminVendors,
          adminComparisons,
          adminNotices,
          showAddQuestionModal,
          showAddVendorModal,
          showAddCompModal,
          showAddNoticeModal,
          fetchAdminCustomSurveys,
          deleteCustomQuestion,
          fetchAdminProcurement,
          fetchAdminCadreNotices,
          deleteCadreNotice,
          adminEmergencySops,
          adminTeamHealthLatest,
          adminRecipes,
          adminRecipeStats,
          adminCentenaryData,
          adminWhitepaper,
          fetchAdminEmergencySops,
          fetchAdminTeamHealth,
          fetchAdminRecipes,
          fetchAdminCentenary,
          pendingHealthLogs,
          healthLeaderboards,
          fetchHealthReviews,
          reviewHealthLog,
          adminWishes,
          adminWishSummary,
          fetchAdminWishes,
          updateWishStatus,
          crawledEvents,
          crawlerSources,
          crawlingLoading,
          fetchCrawlerEvents,
          triggerCrawl,
          importCrawledEvent,
''' + content[ret_idx + len('return {'):]
    print("Inserted feature JS and return bindings!")

with open('app/static/admin.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved updated app/static/admin.html!")
