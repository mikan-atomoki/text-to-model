Fusion 360 を Claude Desktop から直接操作できる MCP (Model Context Protocol) サーバー アドイン。
テキストの指示だけで 3D モデリング・JIS 規格部品の生成が可能です。

## 概要

このプロジェクトはFusion360上でHTTP/SSEベースのMCPサーバーを起動し、Claude Desktop と接続し、モデリングを支援するものです。
64 種類の MCP ツールを通じて、スケッチ作成・押し出し・フィレット・JIS ボルト生成など、幅広い CAD 操作をテキスト指示で実行できます。

## セットアップ

### 必要環境

- Fusion 360
- claude desktop またはclaude code
- Node.js (npx 用)

### インストール

1. このリポジトリをクローンまたはダウンロード

```bash
git clone https://github.com/mikan-atomoki/text-to-model.git
```

2. Fusion 360 のアドインフォルダにコピー

```
# Windows
%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\

# macOS
~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/
```

3. Fusion 360 を起動し、UTILITIES > ADD-INS > Scripts and Add-insから**TextToModel**を実行

4. Claude Desktop の MCP 設定に以下を追加（`.mcp.json` を参照・claude codeなら必要なし）

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "mcp-remote", "http://127.0.0.1:13405/sse"]
    }
  }
}
```

## MCP ツール一覧 (64 tools)

### スケッチ (7)

| ツール | 説明 |
|--------|------|
| `create_sketch` | スケッチ作成 |
| `draw_circle` | 円 |
| `draw_rectangle` | 矩形 |
| `draw_line` | 直線 |
| `draw_arc` | 円弧 |
| `draw_spline` | スプライン |
| `draw_polygon` | 正多角形 |

### フィーチャー (4)

| ツール | 説明 |
|--------|------|
| `extrude` | 押し出し |
| `revolve` | 回転 |
| `sweep` | スイープ |
| `loft` | ロフト |

### 修正 (6)

| ツール | 説明 |
|--------|------|
| `fillet` | フィレット |
| `chamfer` | 面取り |
| `shell` | シェル |
| `mirror` | ミラー |
| `variable_fillet` | 可変フィレット |
| `draft` | 抜き勾配 |

### パターン・結合 (3)

| ツール | 説明 |
|--------|------|
| `circular_pattern` | 円形パターン |
| `rectangular_pattern` | 矩形パターン |
| `combine` | ブーリアン演算 |

### ユーティリティ (9)

| ツール | 説明 |
|--------|------|
| `get_design_info` | ドキュメント情報取得 |
| `list_bodies` | ボディ一覧 |
| `list_components` | コンポーネント一覧 |
| `get_parameters` | パラメータ一覧 |
| `set_parameter` | パラメータ設定 |
| `undo` | 元に戻す |
| `export_step` | STEP エクスポート |
| `export_stl` | STL エクスポート |
| `execute_code` | コード実行 |

### JIS 締結部品 (4)

| ツール | 説明 |
|--------|------|
| `create_jis_bolt` | ボルト (B1176/B1180) |
| `create_jis_nut` | ナット (B1181) |
| `create_jis_screw` | 小ネジ (B1111) |
| `create_jis_washer` | 座金 (B1256) |

### JIS 穴加工 (3)

| ツール | 説明 |
|--------|------|
| `create_threaded_hole` | タップ穴 |
| `create_counterbore_hole` | ザグリ穴 |
| `create_countersink_hole` | 皿ザグリ穴 |

### 機械要素 (3)

| ツール | 説明 |
|--------|------|
| `create_keyway` | キー溝 (B1301) |
| `create_bearing_hole` | ベアリング穴 (B1520) |
| `create_oring_groove` | Oリング溝 (B2401) |

### 構築ジオメトリ (4)

| ツール | 説明 |
|--------|------|
| `create_offset_plane` | オフセット平面 |
| `create_angled_plane` | 角度平面 |
| `create_midplane` | 中間平面 |
| `create_construction_axis` | 構築軸 |

### 検査 (5)

| ツール | 説明 |
|--------|------|
| `list_edges` | エッジ一覧 |
| `list_faces` | フェース一覧 |
| `list_sketches` | スケッチ一覧 |
| `get_body_bounds` | バウンディングボックス |
| `list_construction_planes` | 構築平面一覧 |

### サーフェス (4)

| ツール | 説明 |
|--------|------|
| `patch_surface` | パッチ |
| `thicken_surface` | 厚み付け |
| `offset_surface` | オフセット |
| `boundary_fill` | バウンダリフィル |

### 分割 (2)

| ツール | 説明 |
|--------|------|
| `split_body` | ボディ分割 |
| `split_face` | フェース分割 |

### 変換 (3)

| ツール | 説明 |
|--------|------|
| `move_body` | 移動/回転 |
| `scale_body` | 拡大縮小 |
| `copy_body` | コピー |

### インポート (2)

| ツール | 説明 |
|--------|------|
| `import_svg` | SVG インポート |
| `import_dxf` | DXF インポート |

### 拘束・寸法 (3)

| ツール | 説明 |
|--------|------|
| `add_sketch_constraint` | 幾何拘束 |
| `add_sketch_dimension` | 寸法 |
| `list_sketch_entities` | エンティティ一覧 |

### 外観 (2)

| ツール | 説明 |
|--------|------|
| `set_body_color` | ボディ色設定 |
| `rename_body` | ボディ名変更 |

## ファイル構成

```
TextToModel/
├── TextToModel.py            # エントリーポイント（run / stop）
├── TextToModel.manifest      # Fusion 360 アドインマニフェスト
├── config.json               # サーバー設定（ホスト・ポート・ログレベル）
│
├── mcp/                      # MCP サーバー
│   ├── server.py             # HTTP/SSE サーバー
│   ├── protocol.py           # MCP プロトコル (JSON-RPC)
│   ├── jsonrpc.py            # JSON-RPC リクエスト/レスポンス
│   └── sse_handler.py        # SSE コネクション管理
│
├── bridge/                   # スレッドブリッジ
│   ├── event_bridge.py       # CustomEvent ベースのブリッジ
│   └── executor.py           # ツール実行コーディネーター
│
├── tools/                    # MCP ツール (16 モジュール)
│   ├── __init__.py
│   ├── registry.py           # ツール登録・実行
│   ├── sketch_tools.py
│   ├── feature_tools.py
│   ├── modify_tools.py
│   ├── pattern_tools.py
│   ├── utility_tools.py
│   ├── jis_fastener_tools.py
│   ├── jis_hole_tools.py
│   ├── mechanical_tools.py
│   ├── construction_tools.py
│   ├── inspect_tools.py
│   ├── surface_tools.py
│   ├── split_tools.py
│   ├── transform_tools.py
│   ├── import_tools.py
│   ├── constraint_tools.py
│   └── appearance_tools.py
│
├── data/                     # JIS 規格データ (8 モジュール)
│   ├── jis_threads.py        # ねじ寸法 (M2〜M12)
│   ├── jis_bolts.py          # ボルト (B1176 / B1180)
│   ├── jis_nuts.py           # ナット (B1181)
│   ├── jis_screws.py         # 小ネジ (B1111)
│   ├── jis_washers.py        # 座金 (B1256)
│   ├── jis_keyways.py        # キー溝 (B1301)
│   ├── jis_bearings.py       # ベアリング (B1520)
│   └── jis_orings.py         # O リング (B2401)
│
└── utils/
    └── geometry.py           # mm⇔cm 変換、Point3D ヘルパー
```

## 使用例

Claude Desktop で以下のような指示を出すと、Fusion 360 上にモデルが作成されます。

```
M8x30 の六角穴付きボルトを原点に作成して
```

```
XY 平面に 50mm × 30mm の矩形スケッチを描いて、20mm 押し出して、
上面の長辺エッジに R3 のフィレットを付けて
```

```
直径 20mm の円を描いて回転体を作り、キー溝を追加して
```
