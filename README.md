## 🌲 산불 시뮬레이터

Cellular Automata를 통해 산불의 확산을 시뮬레이션합니다.

### 주요 로직

온도와 습도를 통해 기초 발화 확률을 계산합니다. ($T$: 온도, $H$: 습도)

$$P_{base} = \text{clamp}\left( \frac{1}{1 + \exp(-0.2T + 0.15H + 1.5)}, 0.001, 0.95 \right)$$

이후 무어 이웃을 탐색하며, 인접한 불이 붙은 셀과의 거리에 따른 확률 감소, 그리고 바람의 영향(풍향과 풍속에 따른 확률 증가)을 적용하여 최종 발화 확률을 계산합니다. ($V$: 풍속 계수)

$$P_{final} = P_{base} + \left( w \cdot \frac{V}{10} \cdot \cos(\phi) \right)$$

여기서 $w$는 바람의 영향 계수(불이 붙은 셀과 바람 방향이 일치할 때 1, 반대일 때 0.2), $\phi$는 불이 붙은 셀과 바람 방향 사이의 각도입니다.

이후 난수를 통해 발화 여부를 결정합니다.

### 개발 및 실행

Arch Linux WSL2, Python 3.12.11, uv 0.8.12 환경에서 개발되었습니다.

```bash
pip install -r requirements.txt
streamlit run main.py
```
