<template>
  <v-container class="app-container market-entity-page">
    <!-- 종목 기본 정보 -->
    <v-card
      class="market-entity-summary"
      elevation="0"
    >
      <div class="market-entity-summary__top">
        <div class="market-entity-logo">
          <v-icon
            icon="mdi-ethereum"
            size="30"
          />
        </div>

        <div class="market-entity-summary__content">
          <div class="market-entity-title-row">
            <strong class="market-entity-title">
              Ethereum
            </strong>

            <v-chip
              size="small"
              variant="tonal"
            >
              ETH
            </v-chip>
          </div>

          <div class="market-entity-subtitle">
            이더리움
          </div>
        </div>
      </div>

      <v-divider class="market-entity-divider" />

      <div class="market-entity-info-grid">
        <div class="market-entity-info">
          <div class="market-entity-info__label">
            자산 유형
          </div>

          <div class="market-entity-info__value">
            가상자산
          </div>
        </div>

        <div class="market-entity-info">
          <div class="market-entity-info__label">
            지원 거래소
          </div>

          <div class="market-entity-info__value">
            2개
          </div>
        </div>

        <div class="market-entity-info">
          <div class="market-entity-info__label">
            거래 마켓
          </div>

          <div class="market-entity-info__value">
            3개
          </div>
        </div>
      </div>
    </v-card>

    <!-- 거래소별 마켓 목록 -->
    <section class="market-entity-section">
      <div class="market-entity-section__header">
        <div>
          <div class="market-entity-section__title">
            거래 가능 마켓
          </div>

          <div class="market-entity-section__subtitle">
            Ethereum을 거래할 수 있는 마켓입니다.
          </div>
        </div>

        <span class="market-entity-count">
          3개
        </span>
      </div>

      <div class="mk-list">
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
                  BINANCE
                </v-chip>
              </div>

              <div class="mk-name">
                Ethereum / Tether
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
                  ETH/KRW
                </strong>

                <v-chip
                  size="x-small"
                  variant="tonal"
                >
                  UPBIT
                </v-chip>
              </div>

              <div class="mk-name">
                Ethereum / 원화
              </div>
            </div>

            <div class="mk-change-block">
              <div class="mk-price">
                2,498,000 KRW
              </div>

              <div class="mk-change-up">
                +0.42%
              </div>
            </div>
          </div>

          <div class="mk-row-bottom">
            <span class="mk-volume">
              거래대금 182.4B KRW
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
                  ETH/BTC
                </strong>

                <v-chip
                  size="x-small"
                  variant="tonal"
                >
                  BINANCE
                </v-chip>
              </div>

              <div class="mk-name">
                Ethereum / Bitcoin
              </div>
            </div>

            <div class="mk-change-block">
              <div class="mk-price">
                0.01524 BTC
              </div>

              <div class="mk-change-down">
                -0.61%
              </div>
            </div>
          </div>

          <div class="mk-row-bottom">
            <span class="mk-volume">
              거래대금 4.8K BTC
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