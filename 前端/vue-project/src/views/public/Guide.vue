<template>
  <div class="guide-page">
    <div class="banner">
      <h3>🛡️ 流感科学防治</h3>
      <p>接种疫苗是预防流感最有效的手段</p>
    </div>

    <div class="content">
      <div class="section-title">常见问题</div>
      <el-collapse accordion>
        <el-collapse-item title="😷 甲流和普通感冒有什么区别？" name="1">
          <div class="answer">
            流感（甲流/乙流）通常起病急，高热（39-40℃），伴有畏寒、头痛、肌肉酸痛。而普通感冒症状较轻，一般不发热或低热，以上呼吸道症状为主。
          </div>
        </el-collapse-item>
        <el-collapse-item title="💊 什么时候需要去发热门诊？" name="2">
          <div class="answer">
            如果出现持续高热（超过3天）、呼吸困难、胸痛、神志改变等症状，应立即前往最近的发热门诊就医，避免延误病情。
          </div>
        </el-collapse-item>
        <el-collapse-item title="💉 什么时候接种流感疫苗？" name="3">
          <div class="answer">
            通常建议在每年流感流行季前（9-10月）接种。但如果您错过了，整个流行季节期间都可以接种。
          </div>
        </el-collapse-item>
      </el-collapse>

      <div class="section-title" style="margin-top: 30px;">健康小贴士</div>
      <div class="tips-card">
        <p>1. 勤洗手，使用肥皂或洗手液。</p>
        <p>2. 保持环境清洁和通风。</p>
        <p>3. 在流感高发期，尽量减少去人群聚集场所。</p>
        <p>4. 咳嗽或打喷嚏时，用纸巾遮住口鼻。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-page { min-height: 100vh; background: white; }
.banner { background: #e1f3d8; padding: 30px 20px; color: #2c3e50; }
.banner h3 { margin: 0; color: #67C23A; font-size: 22px; }
.content { padding: 20px; }
.section-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; border-left: 4px solid #409EFF; padding-left: 10px; }
.answer { color: #606266; line-height: 1.6; padding: 10px 0; font-size: 14px; }
.tips-card { background: #f9fafc; padding: 15px; border-radius: 8px; color: #606266; font-size: 14px; line-height: 1.8; }
</style>