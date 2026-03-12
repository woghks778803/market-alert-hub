<template>
  <div class="alert-rules-container">

    <RuleSummary />

    <RuleFilter />

    <div class="alert-rule-list">
      <RuleCard
        v-for="rule in rules"
        :key="rule.id"
        :rule="rule"
      />
    </div>

    <RuleAddFab />

  </div>
</template>

<script setup>
import { ref } from "vue"

import RuleSummary from "@/components/alert/RuleSummary.vue"
import RuleFilter from "@/components/alert/RuleFilter.vue"
import RuleCard from "@/components/alert/RuleCard.vue"
import RuleAddFab from "@/components/alert/RuleAddFab.vue"

const rules = ref([
  {
    id: 1,
    symbol: "BTC/KRW",
    exchange: "UPBIT",
    status: "ON",
    condition: "가격이 50,000,000원 이상",
    cooldown: "5m",
    channels: ["Telegram", "FCM"]
  },
  {
    id: 2,
    symbol: "ETH/USDT",
    exchange: "BINANCE",
    status: "ON",
    condition: "가격이 1,800 USDT 이하",
    cooldown: "10m",
    channels: ["FCM"]
  },
  {
    id: 3,
    symbol: "BTC/KRW",
    exchange: "BINANCE",
    status: "ON",
    condition: "가격이 50,000,000원 이상",
    cooldown: "5m",
    channels: ["Telegram", "FCM"]
  },
  {
    id: 4,
    symbol: "ETH/USDT",
    exchange: "UPBIT",
    status: "ON",
    condition: "가격이 1,800 USDT 이하",
    cooldown: "10m",
    channels: ["FCM"]
  }
])
</script>