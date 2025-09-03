# 🚀 Fast Testing Options

## **1. Quick Single Site Test** (30-60 seconds)
```bash
# Test individual sites quickly
python quick_test.py undp      # UNDP - ~45s
python quick_test.py relief    # ReliefWeb - ~30s  
python quick_test.py ungm      # UNGM - ~35s
python quick_test.py save      # Save the Children - ~30s
python quick_test.py global    # Global Fund - ~25s
python quick_test.py dev       # DevelopmentAid - ~20s (timeout)

# View available sites
python quick_test.py
```

**Output Example:**
```
🧪 Quick testing: UNGM UN Global Marketplace
📍 URL: https://www.ungm.org/Public/Notice
🌐 Loading page... ✅
🔍 Submitting search... ✅
📋 Found: 15 items
📝 Sample: Provision de Vestuario y Lnceria en el marco del p...
✅ WORKING
```

---

## **2. Batch Test All Working Sites** (~5 seconds)
```bash
# Test all 3 working scrapers in parallel
python batch_quick_test.py
```

**Output Example:**
```
🚀 Batch Testing Working Scrapers
========================================

📊 Test Results (Completed in 4.7s):
✅ UNDP  | 750 items | TITLE: Provision of technical assistance...
✅ RELIEF |  20 items | Individual Consultant: Study on the Spre...
✅ UNGM  |  15 items | Provision de Vestuario y Lnceria en el m...

🎯 Summary: 3/3 sites working | 785 total opportunities found
🚀 ALL SYSTEMS GO - Ready for production deployment!
```

---

## **3. Ultra-Fast Selector Test** (10-15 seconds)
```bash
# Test just the selectors without full page analysis
python selector_test.py ungm
python selector_test.py relief  
python selector_test.py undp
```

**Output Example:**
```
⚡ Ultra-fast selector test: UNGM
📦 Container: ✅ #tblNotices .tableBody
📋 Items: 15 found with .tableRow.dataRow.notice-table
  title: ✅ .resultTitle .ungm-title
  organization: ✅ .resultAgency span
  deadline: ✅ .deadline span
  reference: ✅ .resultInfo1[data-description='Reference'] span
⚡ Test completed!
```

---

## **4. Visual Development Mode** (Interactive)
```bash
# Visual browser for debugging and development
python dev_test.py ungm --visual     # Opens browser window
python dev_test.py save --debug      # Visual + slow motion
python dev_test.py relief --slow     # Slow motion, headless

# Just show options
python dev_test.py
```

**Features:**
- 👁 **Visual browser** - See exactly what's happening
- 🐌 **Slow motion** - Watch selectors being tested step by step
- 🎯 **Element highlighting** - Container, items, and fields highlighted in different colors
- 📸 **Error screenshots** - Automatic screenshots if something fails
- ⏰ **Extended inspection time** - Browser stays open for manual review

---

## **5. Production Quick Check** (One-liner)
```bash
# Check if all working scrapers are still operational
python batch_quick_test.py && echo "🚀 READY TO DEPLOY!"
```

---

## **Speed Comparison:**

| Test Type | Duration | Use Case |
|-----------|----------|----------|
| Selector Test | 10-15s | Quick selector validation |
| Single Site | 30-60s | Deep single site analysis |
| Batch Test | ~5s | All working sites health check |
| Dev Mode | Interactive | Visual debugging & development |

---

## **Fastest Workflow for Different Scenarios:**

### **Daily Health Check:**
```bash
python batch_quick_test.py   # 5 seconds, all sites
```

### **Debugging a Broken Site:**
```bash
python dev_test.py save --debug   # Visual + slow for analysis
```

### **Testing New Selectors:**
```bash
python selector_test.py save   # Quick selector validation
```

### **Pre-Deployment Verification:**
```bash
python batch_quick_test.py && python quick_test.py ungm   # Full check
```

---

## **🎯 RECOMMENDED TESTING SEQUENCE:**

1. **Start with Batch Test** (5s) - Overall health check
2. **If issues found**, use **Dev Mode** (visual) - Debug specific sites  
3. **For selector changes**, use **Selector Test** (15s) - Quick validation
4. **Final verification** with **Single Site Test** (60s) - Detailed confirmation

This approach gives you **maximum testing speed** while maintaining **comprehensive coverage**! 🚀
