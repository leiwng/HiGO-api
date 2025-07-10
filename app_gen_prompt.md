# 宠物医疗问诊 API 服务开发需求

你作为一个经验丰富的全栈开发工程师，负责开发一个宠物医疗问诊 API 服务。该服务使用 Python 和 FastAPI 框架，支持文本和图片两种咨询模式。请根据以下需求和技术要求生成完整的 API 服务代码。

## 项目概述

使用 Python + FastAPI 开发一个宠物疾病问答的聊天 API 服务，支持文本咨询和图片咨询两种模式。

## API 接口设计

### 1. 文本咨询 API

**接口路径**: `POST /chat/text`

**输入参数**:

```json
{
  "user_id": "string", // 宠物主人ID
  "conversation_id": "string", // 本轮对话ID
  "pet_id": "string", // 宠物ID
  "question": "string" // 用户咨询文本
}
```

**处理流程**:

1. 获取对话历史记录
2. 应用 RAG 技术检索相关知识
3. 构建最终提示词
4. 调用 ds-vet-answer-32B 模型
5. 流式返回结果并保存

### 2. 图片咨询 API

**接口路径**: `POST /chat/image`

**输入参数**:

```json
{
  "user_id": "string",
  "conversation_id": "string",
  "pet_id": "string",
  "question": "string",
  "images": ["base64_string"] // 图片数组，最多5张
}
```

**处理流程**:

1. 逐一调用 ds-vet-vl-72B 解读图片
2. 获取对话历史和 RAG 知识
3. 整合信息构建提示词
4. 调用 ds-vet-answer-32B 生成回答
5. 流式返回结果并保存

## 外部模型配置

### ds-vet-answer-32B (文本问诊模型)

```python
OPENAI_BASE_URL = "https://gateway.haoshouyi.com/vet1-scope/v1/"
OPENAI_API_KEY = "sk-12qsw3wh19pqhouf6fxmuit"
LLM_MODEL = "ds-vet-answer-32B"
```

### ds-vet-vl-72B (多模态模型)

```python
BASE_URL = "https://platformx.vetmew.com:21006"
API_PATH = "/open/v1/chat"
API_KEY = "vmac8e79f1e084400d"
API_SECRET = "1ghhni82nqzp5jao2umlfnvfium7crqo"
```

## 技术要求

- 使用 FastAPI 框架
- 支持流式输出(Server-Sent Events)
- 实现 HMAC-SHA256 签名认证(多模态 API)
- 错误处理和日志记录
- 异步处理提升性能

## 其他相关事项

### 1. 数据存储相关

- **对话历史存储**：遵从 langchain 和 langgraph 的通用做法和范式对对话历史进行保存。存储的数据库选用 MongoDB。
- **对话数据结构**：参考 langchain 和 langgraph 的通用做法和范式，设计对话数据结构。
- **宠物信息存储**：宠物 ID 对应的宠物信息通过第三方提供的 API 接口获取。具体的接口设计和认证方式参照通用的基于 HTTPs 的 API 接口设计范式进行设计。宠物的信息包括：宠物 ID，宠物名称，品种，年龄，性别，体重，医疗历史（比如绝育，打疫苗，患过哪些重大疾病）

### 2. 多模态 API 实现细节

- **请求格式**：
  多模态 API 的完整请求格式示例代码：

```python
import base64
import hmac
import hashlib
import time
import random
import string
import requests

# 从环境变量或配置中获取
API_KEY = "vmac8e79f1e084400d"
API_SECRET = "1ghhni82nqzp5jao2umlfnvfium7crqo"
BASE_URL = "https://platformx.vetmew.com:21006"
API_PATH = "/open/v1/chat"

def generate_signature(path, body, nonce, timestamp, secret):
    """生成请求签名"""
    data = f"{path}{body}{nonce}{timestamp}".encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')

def call_pet_medical_api():
    """调用宠物医疗API"""
    # 生成随机nonce（8位字母数字）
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # 获取当前时间戳（秒）
    timestamp = str(int(time.time()))

    # 请求体（可根据实际情况修改参数）
    request_body = {
        "msg": "我的狗生病了",
        "breed": 1,
        "birth": "2024-07-01",
        "gender": 1,
        "nick_name": "大黄",
        "fertility": 1
    }

    # 生成签名
    signature = generate_signature(
        API_PATH,
        str(request_body),
        nonce,
        timestamp,
        API_SECRET
    )

    # 设置请求头
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "X-OPENAPI-NONCE": nonce,
        "X-OPENAPI-TIMESTAMP": timestamp,
        "X-OPENAPI-SIGN": signature,
        "Content-Type": "application/json"
    }

    # 发送请求
    try:
        response = requests.post(
            f"{BASE_URL}{API_PATH}",
            json=request_body,
            headers=headers,
            timeout=30
        )
        return response.json(), None
    except Exception as e:
        return None, str(e)

# 示例调用
if __name__ == "__main__":
    result, error = call_pet_medical_api()

    if error:
        print(f"请求失败: {error}")
    else:
        print(f"请求成功，响应内容: {result}")
```

- **多模态 API 类型**：

1. 情绪分析
   访问路径: /open/v1/emotion-recognition
   接口说明：本接口通过图⽚识别动物情绪，返回动物情绪、常⻅原因、养护建议等信息。识别结果以 markdown 格式返回。

1.1 接口调用
1.1.1 请求说明
请求方式：HTTPS POST

1.1.2 请求参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|image|String|否|经过 base64 编码的图像数据，如有编码头(data:image/jpeg;base64)需去掉。⽀持 jpg/jpeg/png 格式|
|url|String|否|图⽚链接。⽀持 jpg/jpeg/png 格式。当 image 存在时，url 失效|

1.1.3 响应说明
请求成功后数据采⽤⾮流式输出，返回 JSON 内容。

1.1.4 响应参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|code||Number|是|错误码|
|msg|String|是|错误信息|
|data|Array[]|是| |
|- text|String|是|识别内容，内容中的'\n'为换⾏符，需适配 markdown 格式|
|- msg_id|String|是|消息 id

1.2 示例
1.2.1 请求⽰例：
{
"url": "https://oss-vetmew.vetmew.com/vetmew/ps/emotion.jpeg"
}
1.2.2 响应⽰例：
{
"code": 0,
"message": "Succeed",
"data": [
{
"text": "###情绪类别:\n 这只巴哥犬表情看起来有些忧郁，眼神中透露出一丝委屈。\n\n###常见原因：\n**健康问题**：可能身体有某些不适，比如皮肤瘙痒、肠胃不适等。\n**缺乏陪伴**：主人长时间不在家，没有足够的互动和玩耍。\n**环境因素**：周围环境过于嘈杂或者温度不适等。\n\n###养护建议：\n 先检查狗狗身体有无异常，如有不适及时带它去看兽医。主人要多花时间陪伴它，陪它玩耍、抚摸它等。给它营造一个舒适安静的环境，保持适宜的温度和湿度等。可以给它一些喜欢的玩具来缓解它的情绪。 ",
"msg_id": "3d136a2c-8aa2-4238-9d75-bb56c14972a7"
}
]
}

2. 粪便分析
   访问路径：/open/v1/feces-recognition
   接口说明：本接口通过粪便图⽚识别动物症状，返回图⽚描述信息、病因、就医建议、⽇常护理建议等信息。识别结果以 markdown 格式返回。

2.1 接口调用

2.1.1 请求说明
请求方式：HTTPS POST

2.1.2 请求参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|image|String|否|经过 base64 编码的图像数据，如有编码头(data:image/jpeg;base64)需去掉。⽀持 jpg/jpeg/png 格式|
|url|String|否|图⽚链接。⽀持 jpg/jpeg/png 格式。当 image 存在时，url 失效|
|breed|Number|是|品种。具体值参考 品种信息表|
|birth|String|是|出⽣⽇期。格式 YYYY-MM-DD|
|gender|Number|是|性别。1 公 2 ⺟|
|fertility|Number|是|⽣育能⼒。1 未绝育 2 已绝育|

2.1.3 响应说明
请求成功后数据采⽤⾮流式输出，返回 JSON 内容。

2.1.4 响应参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|codeNumber 是|错误码|
|msg|String|是|错误信息|
|data|Array[]|是| |
|- text|String|是|识别内容，内容中的'\n'为换⾏符，需适配 markdown 格式|
|- msg_id|String|是|消息 id|

2.2 示例

2.2.1 请求⽰例：
{
"url": "https://oss-vetmew.vetmew.com/vetmew/ps/stool.jpeg",
"breed": 1,
"birth": "2023-07-01",
"gender": 1,
"fertility": 1
}

2.2.2 响应⽰例：
{
"code": 0,
"message": "Succeed",
"data": [
{
"text": "### 图片内容概括\n 图中为两坨不成形的棕黄色粪便，质地看起来较为黏稠，散落在粉色瓷砖地面上。\n\n### 可能的疾病及病因\n- **胃肠炎**\n - 病因：通常由细菌、病毒、寄生虫感染，或饮食不当（如食物变质、突然换粮等）、误食异物等引发，导致胃肠黏膜炎症，影响正常消化功能。\n- **消化不良**\n - 病因：老年犬胃肠功能减弱，一次性进食过多或食物不易消化，会引起消化不良，使粪便性状改变。\n- **胰腺疾病（如胰腺炎）**\n - 病因：胰腺分泌的消化酶异常激活，对胰腺自身及周围组织造成消化，影响消化功能，导致粪便异常。\n- **肠道寄生虫感染**\n - 病因：如蛔虫、绦虫等寄生虫在肠道内寄生、繁殖，影响肠道正常消化吸收，使粪便出现异常。\n\n### 就医建议\n- 及时带狗狗去宠物医院，向兽医详细描述狗狗的饮食、日常行为等情况。\n- 进行粪便检查，确定是否有寄生虫及寄生虫种类。\n- 可能需要进行血液检查、生化检查等，以排查胰腺等器官是否有病变。\n\n### 日常护理建议\n- 保证狗狗饮食的规律性和适量性，避免暴饮暴食，可采用少食多餐的方式。\n- 提供易消化、营养均衡的老年犬专用狗粮。\n- 定期给狗狗进行体内驱虫，根据兽医建议选择合适的驱虫药和驱虫频率。\n- 注意狗狗的饮食卫生，避免喂食变质食物。 \n\n\n\n ",
"msg_id": "754f97bb-4860-4ed6-89c2-5a7a2b526080"
}
]
}

3. ⽪肤分析
   访问路径：/open/v1/skin-recognition
   接口说明：本接口通过⽪肤图⽚识别动物症状，返回图⽚描述信息、病因、就医建议、⽇常护理建议等信息。识别结果以 markdown 格式返回。

3.1 接口调用

3.1.1 请求说明
请求方式：HTTPS POST

3.1.2 请求参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|image|String|否|经过 base64 编码的图像数据，如有编码头(data:image/jpeg;base64)需去掉。⽀持 jpg/jpeg/png 格式|
|url|String|否|图⽚链接。⽀持 jpg/jpeg/png 格式。当 image 存在时，url 失效|
|breed|Number|是|品种。具体值参考 品种信息表|
|birth|String|是|出⽣⽇期。格式 YYYY-MM-DD|
|gender|Number|是|性别。1 公 2 ⺟|
|fertility|Number|是|⽣育能⼒。1 未绝育 2 已绝育|

3.1.3 响应说明
请求成功后数据采⽤⾮流式输出，返回 JSON 内容。

3.1.4 响应参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|code|Number|是|错误码|
|msg|String|是|错误信息|
|data|Array[]|是| |
|- text|String|是|识别内容，内容中的'\n'为换⾏符，需适配 markdown 格式|
|- msg_id|String|是|消息 id|

3.2 示例

3.2.1 请求⽰例：
{
"url": "https://oss-vetmew.vetmew.com/vetmew/ps/skin.jpeg",
"breed": 1,
"birth": "2021-02-01",
"gender": 1,
"fertility": 1
}

3.2.2 响应⽰例：
{
"code": 0,
"message": "Succeed",
"data": [
{
"text": "### 图片内容概括\n 狗狗的皮肤局部出现异常，有类似结痂或皮屑堆积的现象，毛发略显杂乱。\n\n### 可能的疾病及病因\n- **皮肤真菌病**：由犬小孢子菌、石膏样小孢子菌、须毛癣菌等真菌感染引起，通常通过接触感染，如与患病动物接触、共用物品或在潮湿、不卫生的环境中容易感染。\n- **细菌性皮肤病**：如葡萄球菌等细菌感染，常因皮肤损伤、免疫力下降等因素导致细菌侵入皮肤引发炎症。\n- **脂溢性皮炎**：病因可能与遗传、内分泌失调、营养缺乏（如维生素 B 族缺乏）、皮肤脂质代谢异常等有关，导致皮肤油脂分泌过多或过少，引发皮肤炎症和皮屑增多。\n- **湿疹**：多种内外因素引起的皮肤炎症反应，如过敏（食物、环境过敏原等）、皮肤长期潮湿、摩擦、寄生虫叮咬等。\n\n### 就医建议\n- 带狗狗去宠物医院，进行皮肤刮片检查、真菌培养等实验室检查，以确定具体病因。\n- 根据检查结果，遵医嘱使用相应的药物治疗，如抗真菌药、抗生素等。\n\n### 日常护理建议\n- 保持狗狗皮肤清洁干燥，定期用宠物专用沐浴露洗澡，但不要过于频繁。\n- 给狗狗提供营养均衡的食物，可适当补充维生素和脂肪酸等营养物质。\n- 定期梳理毛发，防止毛发打结，同时也能及时发现皮肤异常。\n- 避免狗狗接触患病动物或处于潮湿、脏乱的环境。 ",
"msg_id": "2c4cdf2d-56ac-4485-9bb5-bf9ade85f630"
}
]
}

4. 尿液分析
   访问路径：/open/v1/urine-recognition
   接口说明：本接口通过尿液图⽚识别动物症状，返回图⽚描述信息、病因、就医建议、⽇常护理建议等信息。识别结果以 markdown 格式返回。

4.1 接口调用

4.1.1 请求说明
请求方式：HTTPS POST

4.1.2 请求参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|image|String|否|经过 base64 编码的图像数据，如有编码头(data:image/jpeg;base64)需去掉。⽀持 jpg/jpeg/png 格式|
|url|String|否|图⽚链接。⽀持 jpg/jpeg/png 格式。当 image 存在时，url 失效|
|breed|Number|是|品种。具体值参考 品种信息表|
|birth|String|是|出⽣⽇期。格式 YYYY-MM-DD|
|gender|Number|是|性别。1 公 2 ⺟|
|fertility|Number|是|⽣育能⼒。1 未绝育 2 已绝育|

4.1.3 响应说明
请求成功后数据采⽤⾮流式输出，返回 JSON 内容。

4.1.4 响应参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|code|Number|是|错误码|
|msg|String|是|错误信息|
|data|Array[]|是| |
|- text|String|是|识别内容，内容中的'\n'为换⾏符，需适配 markdown 格式|
|- msg_id|String|是|消息 id|

4.2 示例

4.2.1 请求⽰例：
{
"url": "https://oss-vetmew.vetmew.com/vetmew/ps/tinkle.png",
"breed": 1,
"birth": "2021-02-01",
"gender": 1,
"fertility": 1
}

4.2.2 响应⽰例：
{
"code": 0,
"message": "Succeed",
"data": [
{
"text": "### 图片内容概括\n 尿液呈黄色且其中带有红色的血迹，还存在一些白色的絮状物。\n\n### 可能的疾病及病因\n- **膀胱炎**\n - **病因**：细菌感染、膀胱黏膜受刺激等导致膀胱内壁发炎。\n- **尿道炎**\n - **病因**：细菌、真菌或寄生虫感染尿道，引起尿道炎症。\n- **肾结石**\n - **病因**：尿液中矿物质结晶沉淀，形成结石，划伤尿路导致出血。\n- **膀胱结石**\n - **病因**：类似肾结石，膀胱内形成结石，刺激膀胱黏膜并可能导致出血。\n\n### 就医建议\n- 带狗狗去宠物医院进行全面的尿液检查，包括尿常规、尿沉渣等。\n- 进行泌尿系统的超声检查，查看是否有结石等异常。\n- 根据检查结果，医生可能会给予相应的药物治疗，如消炎药等。\n\n### 日常护理建议\n- 保证狗狗充足的饮水，促进尿液排出，减少结石形成风险。\n- 定期带狗狗进行体检，尤其是泌尿系统的检查。\n- 注意狗狗的饮食均衡，避免高钙、高磷等易导致结石的食物过量摄入。 \n\n\n\n ",
"msg_id": "00f7ca50-a090-48d9-8a61-112b9f44630b"
}
]
}

5. 呕吐物分析
   访问路径：/open/v1/vomitus-recognition
   接口说明：本接口通过呕吐物图⽚识别症状，返回图⽚描述信息、病因、就医建议、⽇常护理建议等信息。识别结果以 markdown 格式返回。

5.1 接口调用

5.1.1 请求说明
请求方式：HTTPS POST

5.1.2 请求参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|image|String|否|经过 base64 编码的图像数据，如有编码头(data:image/jpeg;base64)需去掉。⽀持 jpg/jpeg/png 格式|
|urlString|否|图⽚链接。⽀持 jpg/jpeg/png 格式。当 image 存在时，url 失效|
|breed|Number|是|品种。具体值参考 品种信息表|
|birth|String|是|出⽣⽇期。格式 YYYY-MM-DD|
|gender|Number|是|性别。1 公 2 ⺟|
|fertility|Number|是|⽣育能⼒。1 未绝育 2 已绝育|

5.1.3 响应说明
请求成功后数据采⽤⾮流式输出，返回 JSON 内容。

5.1.4 响应参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|code|Number|是|错误码|
|msg|String|是|错误信息|
|data|Array[]|是|
|- text|String|是|识别内容，内容中的'\n'为换⾏符，需适配 markdown 格式|
|- msg_id|String|是|消息 id|

5.2 示例

5.2.1 请求⽰例：
{
"url": "https://oss-vetmew.vetmew.com/vetmew/ps/vomit.jpeg",
"breed": 1,
"birth": "2024-07-01",
"gender": 1,
"fertility": 1
}

5.2.2 响应⽰例：
{
"code": 0,
"message": "Succeed",
"data": [
{
"text": "### 图片内容概括\n 图中展示的是一滩黄色带有气泡的呕吐物，位于浅色的地面上。\n\n### 可能的疾病及病因\n- **胃炎**\n - 病因：可能因进食刺激性食物、异物、药物等导致胃黏膜发炎。\n- **胃溃疡**\n - 病因：多由应激、药物刺激等因素引起胃黏膜损伤形成溃疡。\n- **胃肠寄生虫感染**\n - 病因：狗狗吞食了含有寄生虫卵的食物或水，寄生虫在胃肠道内繁殖引起。\n- **消化不良**\n - 病因：进食过多、过快，或食物不易消化等。\n\n### 就医建议\n- 尽快带狗狗去宠物医院，向兽医详细描述呕吐的频率、呕吐物的性状等情况。\n- 可能需要进行血液检查、粪便检查等相关检查以确定病因。\n- 遵循兽医的建议进行相应的治疗，如使用止吐药、驱虫药等。\n\n### 日常护理建议\n- 保证狗狗的饮食规律，定时定量喂食。\n- 提供清洁的饮用水，避免狗狗饮用脏水。\n- 避免给狗狗喂食人类的油腻、辛辣等刺激性食物。\n- 定期给狗狗进行体内驱虫。 ",
"msg_id": "e3fbe5c1-a3e1-46a7-badb-3ab7267b6d5e"
}
]
}

6. 耳道分析(Beta)
   访问路径：/open/v1/ear-canal-recognition
   接口说明：本接口通过耳道图⽚识别症状，返回图⽚描述信息、病因、就医建议、⽇常护理建议等信息。识别结果以 markdown 格式返回。

6.1 接口调用

6.1.1 请求说明
请求方式：HTTPS POST

6.1.2 请求参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|image|String|否|经过 base64 编码的图像数据，如有编码头(data:image/jpeg;base64)需去掉。⽀持 jpg/jpeg/png 格式|
|url|String|否|图⽚链接。⽀持 jpg/jpeg/png 格式。当 image 存在时，url 失效|
|breed|Number|是|品种。具体值参考 品种信息表|
|birth|String|是|出⽣⽇期。格式 YYYY-MM-DD|
|gender|Number|是|性别。1 公 2 ⺟|
|fertility|Number|是|⽣育能⼒。1 未绝育 2 已绝育|

6.1.3 响应说明
请求成功后数据采⽤⾮流式输出，返回 JSON 内容。

6.1.4 响应参数：
|字段名|类型|必填|描述|
|:----:|:----:|:----:|:-----|
|code|Number|是 错误码|
|msg|String|是|错误信息|
|data|Array[]|是|
|- text|String|是|识别内容，内容中的'\n'为换⾏符，需适配 markdown 格式|
|- msg_id|String|是|消息 id|

6.2 示例

6.2.1 请求⽰例：
{
"url": "https://oss-vetmew.vetmew.com/vetmew/ps/ear-canal.jpeg",
"breed": 1,
"birth": "2024-07-01",
"gender": 1,
"fertility": 1
}

6.2.2 响应⽰例：
{
"code": 0,
"message": "Succeed",
"data": [
{
"text": "### 图片内容概括\n 图片显示的是狗狗的耳道内部情况。耳道内部可见有黑色和深棕色的分泌物堆积，分泌物呈粘稠状，部分区域附件有耳垢样物质。耳道内壁颜色较正常，但局部有少量分泌物附着，耳道内部结构清晰，未见明显肿胀或溃疡。\n\n---\n\n### 可能的疾病及病因\n1. **耳部感染（细菌或真菌感染）** \n - 病因：耳道分泌物呈黑色和深棕色，可能提示细菌或真菌感染，常见于潮湿环境或卫生不佳。\n\n2. **耳垢积累** \n - 病因：耳道分泌物呈粘稠状，耳垢中含有耳道正常分泌物和耳螨残留物，未及时清理导致积累。\n\n3. **耳螨感染** \n - 病因：耳螨感染可能导致耳道分泌物异常，耳垢中可能存在耳螨或其活动痕迹。\n\n4. **过敏反应或皮肤炎症** \n - 病因：耳道内壁轻微变化，可能提示皮肤炎症或过敏反应，导致耳道分泌物增多。\n\n---\n\n### 就医建议\n1. **尽快就医** \n - 建议带狗狗去宠物医院检查，兽医可通过耳道分泌物采样化验，明确感染类型（细菌或真菌）。\n\n2. **耳道清理和治疗** \n - 医生会进行耳道清理，并根据感染类型开具抗生素或抗真菌药物，必要时进行耳螨治疗。\n\n3. **避免自行清理** \n - 不要自行使用清洁剂或棉签清理耳道，以免加重感染或损伤耳道。\n\n4. **检查整体健康** \n - 如果耳部感染反复发作，需检查狗狗的整体健康状况，包括免疫功能和内分泌系统。\n\n---\n\n### 日常护理建议\n1. **定期检查耳道** \n - 每周检查一次耳道，观察分泌物变化，及时清理耳垢。\n\n2. **保持耳道干燥和卫生** \n - 洗澡时用棉球轻轻塞住耳道口，避免耳道进水。洗耳时使用宠物专用耳道清洁液。\n\n3. **避免耳螨感染** \n - 定期检查耳道，保持耳道清洁，减少耳螨滋生的机会。\n\n4. **注意环境卫生** \n - 保持家中环境清洁，避免过敏原（如灰尘、花粉）刺激耳道。\n\n",
"msg_id": "429c58f2-a960-4b27-92aa-fed6fc338849"
}
]
}

- **图片处理**：
  需要经过 base64 编码的图像数据，如有编码头(data:image/jpeg;base64)需去掉。⽀持 jpg/jpeg/png 格式。

### 3. API 接口设计

- **响应格式**：API 返回的数据结构，以及除了回答内容还需要返回的信息。

1. 标准成功响应
   {
   "success": True,
   "data": {...},
   "message": "操作成功"
   }

2. 错误响应
   {
   "success": False,
   "error": "错误信息",
   "detail": "详细错误描述"
   }

3. 支持流式响应
   Chat 接口的流式响应代码示例：

```python
@app.post("/chat")
async def chat_endpoint():
    # 返回 StreamingResponse
    return StreamingResponse(
        stream_chat_response(messages, user_id),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )

# 流式响应格式
async def stream_chat_response(messages, user_id):
    for chunk in response_stream:
        yield f"data: {json.dumps(chunk)}\n\n"
```

- **错误处理**：通过全局异常处理，处理局部异常处理漏掉的异常。局部的具体异常根据异常类型进行处理，比如：文件上传异常，图片处理错误异常，模型调用异常，第三方 API 服务调用异常。

- **认证机制**：使用 JWT 令牌认证，支持 OAuth2.0 协议。

### 4. 技术架构细节

- **并发处理**：按照当前业界的成熟方案进行处理。

- **缓存策略**：需要对模型响应进行缓存。

- **日志记录**：使用 Loguru 库进行日志记录。需要日志记录的操作有：a.前端请求引发的操作步骤；b.调用外部 API 接口，包括发起请求和接收到响应的时间戳，以及调用耗时。

- **宠物信息 API**: 第三方宠物信息 API 的具体接口格式和认证方式

1. 接口调用规范
   BASE_URL: https://api.pet-info-service.com/v1 （示例地址）
   认证方式: HMAC-SHA256 签名认证
   请求头:
   Authorization: HMAC-SHA256 Credential={client_id}
   X-Timestamp={timestamp}
   X-Signature={calculated_signature}
   数据格式: JSON（Content-Type: application/json）
   请求方法: GET/POST
   超时设置: 建议 5000ms，最大重试 2 次

2 具体接口示例：
2.1 获取宠物基本信息

```http
GET /pets/{pet_id}
Headers:
  Authorization: HMAC-SHA256 Credential=CLIENT12345
  X-Timestamp: 1633024000
  X-Signature: 7a038d8e...（64位签名）
```

2.2 响应示例：

```json
{
  "data": {
    "pet_id": "PET_1234567",
    "name": "Buddy",
    "species": "canine",
    "breed": "Golden Retriever",
    "age": 5,
    "weight": 28.5,
    "vaccination_records": [
      { "vaccine": "Rabies", "date": "2023-01-15" },
      { "vaccine": "DHPP", "date": "2023-03-20" }
    ],
    "medical_history": [{ "date": "2022-08-10", "diagnosis": "Ear infection" }]
  },
  "last_updated": "2023-08-15T09:30:00Z"
}
```

- **图片分类逻辑**: 如何自动判断上传的图片应该调用哪个多模态 API 端点？是否需要用户指定类型？
  用户上传图片时会指定图片类型，来确定调用哪个多模态 API 端点。

- **宠物品种映射**: 多模态 API 中的 breed 参数值与实际宠物品种的对应关系表在哪里？
  有专门的文件 pet_breed_0dd7f7.json 来保存宠物品种的对应关系，其示例数据如下：

```json
[
  {
    "id": 1,
    "name": "阿富汗猎犬",
    "category": "狗"
  },
  {
    "id": 2,
    "name": "阿卡巴士犬",
    "category": "狗"
  },
  {
    "id": 3,
    "name": "阿拉斯加雪橇犬",
    "category": "狗"
  },
...
  {
    "id": 421,
    "name": "三花猫",
    "category": "猫"
  }
]
```

- **部署环境**: 服务部署在什么环境？需要 Docker 化吗？
  服务部署在 UCloud 共有云上，需要 Docker 化。

- **并发限制**: 对外部 API 的调用是否有频率限制？需要实现限流吗？
  外部 API 的调用需要有频率限制，需要实现限流。

**_请务必仔细、认真准确的分析上面提到的每一条需求和技术要求细节，并基于以上内容生成完整的 API 服务代码，包括项目结构、依赖配置、核心业务逻辑和工具函数。_**

```

```
