<template>
  <v-container class="app-container market-entity-page">
    <!-- 거래소 기본 정보 -->
    <v-card
      class="market-entity-summary"
      elevation="0"
    >
      <div class="market-entity-summary__top">
        <div class="market-entity-logo">
          <v-icon
            icon="mdi-swap-horizontal-bold"
            size="28"
          />
        </div>

        <div class="market-entity-summary__content">
          <div class="market-entity-title-row">
            <strong class="market-entity-title">
              Binance
            </strong>

            <v-chip
              size="small"
              variant="tonal"
            >
              BINANCE
            </v-chip>
          </div>

          <div class="market-entity-subtitle">
            바이낸스
          </div>
        </div>

        <v-btn
          icon="mdi-open-in-new"
          variant="text"
          color="medium-emphasis"
          aria-label="거래소 홈페이지 열기"
        />
      </div>

      <v-divider class="market-entity-divider" />

      <div class="market-entity-info-grid">
        <div class="market-entity-info">
          <div class="market-entity-info__label">
            국가
          </div>

          <div class="market-entity-info__value">
            Global
          </div>
        </div>

        <div class="market-entity-info">
          <div class="market-entity-info__label">
            시간대
          </div>

          <div class="market-entity-info__value">
            UTC
          </div>
        </div>

        <div class="market-entity-info">
          <div class="market-entity-info__label">
            거래 마켓
          </div>

          <div class="market-entity-info__value">
            426개
          </div>
        </div>
      </div>
    </v-card>

    <!-- 마켓 목록 -->
    <section class="market-entity-section">
      <div class="market-entity-section__header">
        <div>
          <div class="market-entity-section__title">
            거래 가능 마켓
          </div>

          <div class="market-entity-section__subtitle">
            Binance에서 지원하는 마켓입니다.
          </div>
        </div>

        <span class="market-entity-count">
          426개
        </span>
      </div>

      <v-text-field
        class="mk-search"
        density="compact"
        variant="solo"
        flat
        clearable
        hide-details
        prepend-inner-icon="mdi-magnify"
        placeholder="심볼 또는 종목명 검색"
      />

      <div class="mk-list">
        <v-card
          class="mk-card market-entity-market-card"
          elevation="0"
        >
          <div class="mk-row-top">
            <div>
              <div class="market-entity-symbol-row">
                <strong class="mk-symbol">
                  BTC/USDT
                </strong>

                <v-chip
                  size="x-small"
                  variant="tonal"
                >
                  BTC
                </v-chip>
              </div>

              <div class="mk-name">
                Bitcoin · 비트코인
              </div>
            </div>

            <div class="mk-change-block">
              <div class="mk-price">
                118,420 USDT
              </div>

              <div class="mk-change-up">
                +1.24%
              </div>
            </div>
          </div>

          <div class="mk-row-bottom">
            <span class="mk-volume">
              거래대금 2.8B USDT
            </span>

            <v-icon
              icon="mdi-chevron-right"
              size="20"
              color="medium-emphasis"
            />
          </div>
        </v-card>

        <v-card
          class="mk-card market-entity-market-card"
          elevation="0"
        >
          <div class="mk-row-top">
            <div>
              <div class="market-entity-symbol-row">
                <strong class="mk-symbol">
                  ETH/USDT
                </strong>

                <v-chip
                  size="x-small"
                  variant="tonal"
                >
                  ETH
                </v-chip>
              </div>

              <div class="mk-name">
                Ethereum · 이더리움
              </div>
            </div>

            <div class="mk-change-block">
              <div class="mk-price">
                1,806 USDT
              </div>

              <div class="mk-change-down">
                -0.03%
              </div>
            </div>
          </div>

          <div class="mk-row-bottom">
            <span class="mk-volume">
              거래대금 2.7B USDT
            </span>

            <v-icon
              icon="mdi-chevron-right"
              size="20"
              color="medium-emphasis"
            />
          </div>
        </v-card>

        <v-card
          class="mk-card market-entity-market-card"
          elevation="0"
        >
          <div class="mk-row-top">
            <div>
              <div class="market-entity-symbol-row">
                <strong class="mk-symbol">
                  SOL/USDT
                </strong>

                <v-chip
                  size="x-small"
                  variant="tonal"
                >
                  SOL
                </v-chip>
              </div>

              <div class="mk-name">
                Solana · 솔라나
              </div>
            </div>

            <div class="mk-change-block">
              <div class="mk-price">
                162.42 USDT
              </div>

              <div class="mk-change-up">
                +2.18%
              </div>
            </div>
          </div>

          <div class="mk-row-bottom">
            <span class="mk-volume">
              거래대금 846.3M USDT
            </span>

            <v-icon
              icon="mdi-chevron-right"
              size="20"
              color="medium-emphasis"
            />
          </div>
        </v-card>
      </div>
    </section>
  </v-container>
</template>