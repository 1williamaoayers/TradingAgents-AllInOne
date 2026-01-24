# yfinance 1810.HK 数据结构分析报告

## 测试时间
2026-01-24

## 测试环境
Docker容器: tradingagents

---

## 一、基本信息

- **数据类型**: `<class 'list'>` (Python列表)
- **新闻数量**: 10条
- **是否为空**: False

---

## 二、数据结构

### 2.1 顶层结构
每条新闻包含2个键:
- `id`: 新闻唯一标识符
- `content`: 新闻内容对象

### 2.2 content字段包含的17个子字段
```
1. id - 内容ID
2. contentType - 内容类型 (STORY)
3. title - 标题
4. description - 描述
5. summary - 摘要
6. pubDate - 发布日期
7. displayTime - 显示时间
8. isHosted - 是否托管
9. bypassModal - 是否绕过模态框
10. previewUrl - 预览URL
11. thumbnail - 缩略图对象
12. provider - 来源信息
13. canonicalUrl - 规范URL
14. clickThroughUrl - 点击跳转URL
15. metadata - 元数据
16. finance - 财经相关信息
17. storyline - 故事线
```

---

## 三、第1条新闻完整示例

```json
{
  "id": "1c814e16-2ad0-3abd-94d4-0d788a576872",
  "content": {
    "id": "1c814e16-2ad0-3abd-94d4-0d788a576872",
    "contentType": "STORY",
    "title": "Assessing Xiaomi's (SEHK:1810) Valuation After New 7 Year Low Interest EV Financing Plan",
    "description": "",
    "summary": "Xiaomi (SEHK:1810) is drawing fresh attention after launching a 7 year low interest financing plan for its electric vehicles...",
    "pubDate": "2026-01-20T01:08:23Z",
    "displayTime": "2026-01-20T01:08:23Z",
    "isHosted": true,
    "bypassModal": false,
    "previewUrl": null,
    "thumbnail": {
      "originalUrl": "https://media.zenfs.com/en/simply_wall_st__316/4ede54afa2108a12bdee07c0b0d94a59",
      "originalWidth": 1194,
      "originalHeight": 432
    },
    "provider": {
      "displayName": "Simply Wall St.",
      "url": "https://simplywall.st/"
    },
    "canonicalUrl": {
      "url": "https://finance.yahoo.com/news/assessing-xiaomi-sehk-1810-valuation-010823573.html",
      "site": "finance",
      "region": "US",
      "lang": "en-US"
    }
  }
}
```

---

## 四、10条新闻列表

| 序号 | 标题 | 来源 | 发布时间 |
|------|------|------|----------|
| 1 | Assessing Xiaomi's (SEHK:1810) Valuation After New 7 Year Low Interest EV Financing Plan | Simply Wall St. | 2026-01-20T01:08:23Z |
| 2 | Apple regains top spot in China as iPhone shipments soar 22% | GuruFocus.com | 2026-01-19T15:34:43Z |
| 3 | Micron Flags Unprecedented Memory Shortage | GuruFocus.com | 2026-01-19T11:48:05Z |
| 4 | Porsche Deliveries Drop 10% as China Slump and EV Weakness Bite | GuruFocus.com | 2026-01-16T17:47:17Z |
| 5 | Chinese EVs inch closer to the US as Canada slashes tariffs | TechCrunch | 2026-01-16T16:04:02Z |
| 6 | The Bull Case For Xiaomi (SEHK:1810) Could Change Following India's Proposed Smartphone Source-Code Rules | Simply Wall St. | 2026-01-15T22:11:51Z |
| 7 | India's security plan could create a new headache for iPhone and Android users | TheStreet | 2026-01-14T17:33:00Z |
| 8 | Is Xiaomi (SEHK:1810) Attractive After Recent Share Price Weakness? | Simply Wall St. | 2026-01-13T00:17:39Z |
| 9 | Xiaomi Is No Longer a Handset OEM -- But the Market Still Prices It Like One | GuruFocus.com | 2026-01-12T13:12:47Z |
| 10 | Apple Leads Global Smartphone Market With 20% Share in 2025 | GuruFocus.com | 2026-01-12T11:38:54Z |

---

## 五、关键字段说明

### 5.1 标题字段 (title)
```
"Assessing Xiaomi's (SEHK:1810) Valuation After New 7 Year Low Interest EV Financing Plan"
```

### 5.2 摘要字段 (summary)
```
"Xiaomi (SEHK:1810) is drawing fresh attention after launching a 7 year low interest financing plan for its electric vehicles, targeting first time buyers and raising questions about future demand and margin sensitivity..."
```

### 5.3 链接字段 (canonicalUrl)
```
https://finance.yahoo.com/news/assessing-xiaomi-sehk-1810-valuation-010823573.html
```

### 5.4 发布时间 (pubDate)
```
2026-01-20T01:08:23Z
```

### 5.5 来源 (provider.displayName)
```
Simply Wall St.
```

---

## 六、结论

yfinance对`1810.HK`返回的数据是:

1. **类型**: Python列表 (list)
2. **内容**: 10个完整的新闻对象
3. **结构**: 每个对象包含17个字段的详细信息
4. **可用性**: 包含标题、摘要、链接、时间、来源等所有必要信息
5. **格式**: 标准JSON结构，可直接用于分析

**对比**:
- `01810.HK` (带前导0) → 返回空列表 `[]`
- `1810.HK` (不带前导0) → 返回10条完整新闻

这证明了yfinance修复的有效性：去除前导0后，yfinance能够正确返回完整的新闻数据。
