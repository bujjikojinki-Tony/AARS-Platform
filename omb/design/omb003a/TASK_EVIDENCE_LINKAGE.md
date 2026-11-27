# WP-07 Evidence与任务关联

复用Core Observation→Evidence→Claim→Decision→Outcome等引用模型和SDK certify。Task只增加管理关系，不替代或扩写已有业务对象类型。Core status=ACTIVE、Knowledge=ACCEPTED或certification_level=CERTIFIED都不是任务人工批准。

接入路径：操作者指定的可信适配器读取获准来源→保留原始字节/查询条件/采集时间→生成完整Core对象与引用闭包→SDK certify→计算存储canonical hash→登记不可变ObjectSnapshot→Bot只能按snapshot_id提出关联→Task服务再次核查来源与用途→生成TaskEvidenceLinkVersion。原始字节hash、Core对象存储hash、对象图digest和任务证据集合hash分别记录，不互相替代。

当前002原图Provenance.content_hash可能为sha256:unavailable。它可作为明确标注的合成测试fixture，由已核实归档/SQLite记录重算存储hash并登记FIXTURE_VERIFIED；不得补写假原始来源hash或宣称真实观测。现有Store.seed仅允许9对象test_fixture，003不得修改这一准入条件去接受真实数据。

|约束|判定|
|---|---|
|仅Observation快照|不能作为Evidence关联；需要SDK明确构造Evidence并有Observation引用|
|Core图缺失父对象/类型错误|拒绝登记或关联，保留失败原因摘要|
|存储hash相符但来源不可核验|source_verification=UNVERIFIED，不能进入结果审核的可用证据集合|
|目录资源PENDING|只允许目录元数据引用，不能生成研究Evidence或批准采集|
|Evidence为合成且Task是研究/真实采集|用途不符，拒绝；当前根本不开放研究/生产purpose|
|许可撤销/过期/用途改变|追加link版本，use_state=REVOKED/REVIEW_REQUIRED；使待review失效；不删除对象与历史决定|
|重复同一Task+snapshot关联|按服务定义返回已有link，不创建重复边；新幂等键的无变化操作返回NO_CHANGE|
|对象ID相同但新内容|保留不同snapshot_id；需显式supersedes与重新校验，禁止原地改快照|

canonical采用冻结Store.canonical的UTF-8、sort_keys、紧凑分隔符、ensure_ascii=false、allow_nan=false，标识为AARS_CANONICAL_JSON_V1，不宣称RFC8785符合性。Core既有浮点值沿用已固定Python/序列化版本；新管理字段不接受NaN/Infinity，计量精度值使用带单位的十进制文本，禁止跨语言重编码后假定hash不变。

evidence_set_hash覆盖排序后的(link_id,revision,snapshot_id,use_state,purpose,scope_hash,verification_record_hash)列表；其中verification_record含许可依据与有效期限。Review snapshot绑定definition_hash、evidence_set_hash、Task.version、attempt和policy_version。签名后来源状态变化即REVIEW_STALE，不能仅凭“当时看过数据”继续批准。

冻结例子仅引用OMB-SIM-BotAcceptance已有1个Evidence及其Observation闭包，共9个原图对象；不构造新的观测值或研究结论。首次关联的可用等级只能USABLE_FIXTURE。TaskEvidenceLink不自动生成Claim或Knowledge；人工批准只接受该次任务交付，不等同科学命题已成立。

## 指纹输入与审计链

- definition_hash覆盖规范化title、description、purpose、owner_principal_id、priority、due_at和用途scope；不含Task.version或updated_at。
- authorization_scope_hash覆盖workspace/policy版本及排序后的有效TaskAcl/binding版本；任一范围变化使既有review失效。
- event_hash覆盖event除event_hash外的所有规范字段（含payload、prev_hash、from/to状态与版本、actor和request hash），首prev_hash固定为sha256:后接64个0。不能把自身hash再放入被hash内容。
- ReviewRequest.evidence_set_hash和授权scope hash取请求审核事务中的同一快照，不在签名阶段重新悄悄换成“最新值”。

源对象Core Provenance.content_hash与ObjectSnapshot.snapshot_id用途不同，禁止用后者覆盖前者。Snapshot canonical bytes与原始字节可以分别散列，图digest覆盖排序后的(object_id,snapshot_id)闭包。Schema只校验形状，哈希重算、外键、时间和签名是未来语义验证器的强制检查。
