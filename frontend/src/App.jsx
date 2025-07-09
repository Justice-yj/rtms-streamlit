import React, { useState, useEffect, useRef } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
  Slider,
  Paper,
  useMediaQuery
} from '@mui/material';
import { createTheme, ThemeProvider, useTheme } from '@mui/material/styles';
import { Map, View } from 'ol';
import TileLayer from 'ol/layer/Tile';
import XYZ from 'ol/source/XYZ';
import { fromLonLat } from 'ol/proj';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import { Icon, Style } from 'ol/style';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import 'ol/ol.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// App 컴포넌트 외부에 커스텀 테마 정의
const customTheme = createTheme({
  palette: {
    primary: {
      main: '#3f51b5', // 기존 Material Blue (조금 더 차분한 색으로 변경 가능)
      // main: '#1976d2', // 예시: 더 밝은 파랑
      // main: '#004d40', // 예시: 짙은 녹색 계열
    },
    secondary: {
      main: '#ff4081', // 예시: 강조색
    },
    background: {
      default: '#f4f6f8', // 약간 회색빛이 도는 배경색
      paper: '#ffffff', // Paper 컴포넌트 배경색
    },
  },
  typography: {
    fontFamily: [
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      // 한글 폰트 추가 (시스템 폰트 우선)
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
      '"Noto Sans KR"', // Noto Sans KR이 설치되어 있다면 사용
    ].join(','),
    h6: {
      fontWeight: 600, // 제목 글씨를 좀 더 두껍게
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#2c3e50', // 어두운 네이비/회색 계열 앱바
          // backgroundColor: '#1a237e', // 더 진한 남색
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none', // 탭 글씨 대문자 변환 방지
          fontWeight: 600,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.05)', // 부드러운 그림자
          borderRadius: '8px', // 둥근 모서리
        },
      },
    },
  },
});

// 탭 패널 컴포넌트
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3, width: '100%' }}>
          <Typography component="div">{children}</Typography>
        </Box>
      )}
    </div>
  );
}

function a11yProps(index) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [cities, setCities] = useState({});
  const [selectedCity, setSelectedCity] = useState('');
  const [districts, setDistricts] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [lawdCd, setLawdCd] = useState('');
  const [startYM, setStartYM] = useState('');
  const [endYM, setEndYM] = useState('');
  const [aptName, setAptName] = useState('');
  const [exclusiveAreaRange, setExclusiveAreaRange] = useState([0, 200]); // 전용면적 슬라이더 상태
  const [tradeData, setTradeData] = useState([]);
  const [geocodedTradeData, setGeocodedTradeData] = useState([]);
  const [forecastData, setForecastData] = useState(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const mapElement = useRef(null);
  const mapInstance = useRef(null);
  const [error, setError] = useState(null);

  // 컬럼 표시 이름 및 제외 목록 정의
  const columnDisplayNames = {
    "deal_year": "년",
    "deal_month": "월",
    "deal_day": "일",
    "sigungu_code": "시군구코드",
    "lawd_dong_code": "법정동코드",
    "apartment_name": "아파트",
    "deal_amount": "거래금액",
    "area_exclusive": "전용면적",
    "floor": "층",
    "build_year": "건축년도",
    "road_name": "도로명",
    "dong": "법정동",
    "jibun": "지번",
    "cancel_deal_day": "거래취소일",
    "cancel_deal_type": "거래취소유형",
    "req_gbn": "요청구분",
    "rnum": "순번",
  };

  const columnsToExclude = [
    "sigungu_name", // 시군구명은 법정동과 중복되거나 불필요할 수 있음
    "lawd_dong_name", // 법정동명은 법정동과 중복되거나 불필요할 수 있음
    "deal_ymd", // 년월일로 분리되어 있으므로 불필요
    "bonbun", // 지번과 중복될 수 있음
    "bubun", // 지번과 중복될 수 있음
    "danji_name", // 아파트 이름과 중복
    "exclusive_area", // 전용면적과 중복
    "floor_num", // 층과 중복
    "house_type", // 주택 유형 (아파트만 다루므로 불필요)
    "req_gbn_name", // 요청구분과 중복
    "rnum_str", // 순번과 중복
    "sigungu_cd", // 시군구코드와 중복
    "lawd_cd", // 법정동코드와 중복
    "deal_y", // 년과 중복
    "deal_m", // 월과 중복
    "deal_d", // 일과 중복
    "build_y", // 건축년도와 중복
    "road_name_cd", // 도로명코드 불필요
    "road_name_bonbun", // 도로명본번 불필요
    "road_name_bubun", // 도로명부번 불필요
    "road_name_seq", // 도로명일련번호 불필요
    "road_name_addr", // 도로명주소와 중복
    "dong_code", // 법정동코드와 중복
    "jibun_main", // 지번과 중복
    "jibun_sub", // 지번과 중복
    "latitude", // 지도 시각화에 사용되므로 테이블에서는 제외
    "longitude", // 지도 시각화에 사용되므로 테이블에서는 제외
  ];

  // 숫자 파싱 헬퍼 함수 (콤마 제거 및 숫자로 변환)
  const parseNumber = (value) => {
    if (value === null || value === undefined) {
      return null; // null 또는 undefined인 경우 null 반환
    }
    if (typeof value === 'string') {
      const parsed = Number(value.replace(/,/g, ''));
      return isNaN(parsed) ? null : parsed; // 파싱 실패 시 null 반환
    }
    return value; // 이미 숫자인 경우 그대로 반환
  };

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // LAWD_CODES 로드
  useEffect(() => {
    const fetchLawdCodes = async () => {
      try {
        const response = await fetch(`${API_URL}/lawd-codes`);
        if (!response.ok) {
          throw new Error('법정동 코드 데이터를 불러오는데 실패했습니다.');
        }
        const data = await response.json();
        setCities(data);
      } catch (err) {
        console.error("법정동 코드 로드 오류:", err);
        setError("법정동 코드 데이터를 불러오는데 실패했습니다.");
      }
    };

    fetchLawdCodes();

    const today = new Date();
    const year = today.getFullYear();
    const month = (today.getMonth() + 1).toString().padStart(2, '0');
    setStartYM(`${year}${month}`);
    setEndYM(`${year}${month}`);
  }, []);

  // 시/도 선택 시 시/군/구 업데이트
  useEffect(() => {
    const fetchDistricts = async () => {
      if (selectedCity) {
        try {
          const response = await fetch(`${API_URL}/sgg-list/${selectedCity}`);
          if (!response.ok) {
            throw new Error('시/군/구 데이터를 불러오는데 실패했습니다.');
          }
          const data = await response.json();
          setDistricts(data);
          setSelectedDistrict(''); // 시/도 변경 시 시/군/구 초기화
        } catch (err) {
          console.error("시/군/구 로드 오류:", err);
          setError("시/군/구 데이터를 불러오는데 실패했습니다.");
        }
      }
    };

    fetchDistricts();
  }, [selectedCity]);

  // 시/군/구 선택 시 법정동 코드 업데이트 (이 부분은 백엔드에서 직접 코드를 가져오지 않으므로 변경 없음)
  useEffect(() => {
    // 백엔드에서 직접 법정동 코드를 가져오는 API가 없으므로,
    // 여기서는 선택된 시/도와 시/군/구를 조합하여 법정동 코드를 유추하거나,
    // 별도의 API 호출이 필요합니다.
    // 현재는 `handleSearch`에서 `lawdCd`를 사용하므로, 이 값만 설정하면 됩니다.
    // 실제 법정동 코드는 `handleSearch`에서 `get_district_code` API를 통해 가져와야 합니다.
    // 여기서는 단순히 선택된 시/도와 시/군/구 조합으로 `lawdCd`를 설정합니다.
    // 이 부분은 백엔드 API 설계에 따라 달라질 수 있습니다.
    // 임시로 `selectedCity`와 `selectedDistrict`를 조합하여 `lawdCd`를 설정합니다.
    // 실제 법정동 코드는 `get_district_code` API를 통해 가져와야 합니다.
    // 이 부분은 `handleSearch` 함수에서 처리하도록 합니다.
    setLawdCd(''); // 초기화
  }, [selectedCity, selectedDistrict]);

  // OpenLayers 지도 초기화 및 마커 추가
  useEffect(() => {
    if (mapElement.current && geocodedTradeData.length > 0) {
      // VWorld API 키를 .env 파일에 VITE_VWORLD_API_KEY로 설정하세요.
      const vworldApiKey = import.meta.env.VITE_VWORLD_API_KEY;

      if (!vworldApiKey) {
        setError("VWorld API 키가 설정되지 않았습니다. frontend/.env 파일에 VITE_VWORLD_API_KEY를 추가해주세요.");
        return;
      }

      const initialCenter = fromLonLat([geocodedTradeData[0].longitude, geocodedTradeData[0].latitude]);

      const vworldLayer = new TileLayer({
        source: new XYZ({
          url: `https://api.vworld.kr/req/wmts/1.0.0/${vworldApiKey}/Base/{z}/{y}/{x}.png`,
          crossOrigin: 'anonymous',
        }),
      });

      const vectorSource = new VectorSource();
      const vectorLayer = new VectorLayer({
        source: vectorSource,
      });

      mapInstance.current = new Map({
        target: mapElement.current,
        layers: [vworldLayer, vectorLayer],
        view: new View({
          center: initialCenter,
          zoom: 16,
        }),
      });

      // 마커 추가
      geocodedTradeData.forEach(data => {
        if (data.longitude && data.latitude) {
          const marker = new Feature({
            geometry: new Point(fromLonLat([data.longitude, data.latitude])),
          });

          marker.setStyle(
            new Style({
              image: new Icon({
                anchor: [0.5, 1],
                src: 'https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/icon.png', // 기본 마커 이미지
              }),
            })
          );
          vectorSource.addFeature(marker);
        }
      });

      return () => {
        if (mapInstance.current) {
          mapInstance.current.setTarget(undefined);
          mapInstance.current = null;
        }
      };
    } else if (mapInstance.current) {
      // 데이터가 없으면 지도 초기화
      mapInstance.current.setTarget(undefined);
      mapInstance.current = null;
    }
  }, [geocodedTradeData]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setTradeData([]);
    setGeocodedTradeData([]);
    setForecastData(null);

    if (!selectedCity || !selectedDistrict || !startYM || !endYM) {
      setError("모든 필수 입력 필드를 채워주세요.");
      setLoading(false);
      return;
    }

    try {
      // 법정동 코드 가져오기
      const districtCodeResponse = await fetch(`${API_URL}/district-code?sido=${selectedCity}&district_name=${selectedDistrict}`);
      if (!districtCodeResponse.ok) {
        const errorData = await districtCodeResponse.json();
        throw new Error(errorData.detail || "법정동 코드를 가져오는데 실패했습니다.");
      }
      const districtCodeData = await districtCodeResponse.json();
      const fetchedLawdCd = districtCodeData.district_code;
      setLawdCd(fetchedLawdCd); // 상태 업데이트

      const [minArea, maxArea] = exclusiveAreaRange;
      const tradeResponse = await fetch(`${API_URL}/trade-data?lawd_cd=${fetchedLawdCd}&start_ym=${startYM}&end_ym=${endYM}${aptName ? `&apt_name=${aptName}` : ''}&min_area=${minArea}&max_area=${maxArea}`);
      if (!tradeResponse.ok) {
        const errorData = await tradeResponse.json();
        throw new Error(errorData.detail || "거래 데이터 조회 실패");
      }
      const tradeDataResult = await tradeResponse.json();
      setTradeData(tradeDataResult);
      console.log("Raw tradeDataResult:", tradeDataResult); // 디버깅용 로그 추가

      if (tradeDataResult.length > 0) {
        const geocodeResponse = await fetch(`${API_URL}/geocode-trade-history`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ trade_data: tradeDataResult }),
        });

        if (!geocodeResponse.ok) {
          const errorData = await geocodeResponse.json();
          throw new Error(errorData.detail || "지오코딩 데이터 조회 실패");
        }
        const geocodedDataResult = await geocodeResponse.json();
        setGeocodedTradeData(geocodedDataResult);
      } else {
        setGeocodedTradeData([]);
      }

    } catch (err) {
      setError(err.message);
      console.error("데이터 조회 오류:", err);
    } finally {
      setLoading(false);
    };
  };

  const handleForecast = async () => {
    console.log("handleForecast function called."); // 함수 호출 확인 로그
    setLoading(true);
    setError(null);
    setForecastData(null);

    if (tradeData.length === 0) {
      setError("예측을 위한 거래 데이터가 없습니다. 먼저 데이터를 조회해주세요.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/forecast`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ trade_data: tradeData, periods: 12 }), // 12개월 예측
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "가격 예측 실패");
      }
      const data = await response.json();
      console.log("Received forecast data from backend:", data); // 백엔드 응답 로그 추가
      setForecastData(data);
    } catch (err) {
      console.error("가격 예측 오류 (handleForecast):", err); // 오류 로그 추가
      setError(err.message);
      console.error("가격 예측 오류:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    setLoading(true);
    setError(null);
    setAnswer('');

    if (tradeData.length === 0) {
      setError("챗봇을 위한 거래 데이터가 없습니다. 먼저 데이터를 조회해주세요.");
      setLoading(false);
      return;
    }

    if (!question.trim()) {
      setError("질문을 입력해주세요.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ trade_data: tradeData, question: question }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "챗봇 응답 실패");
      }
      const data = await response.json();
      setAnswer(data.answer);
    } catch (err) {
      setError(err.message);
      console.error("챗봇 오류:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ThemeProvider theme={customTheme}> {/* 이 부분 추가 */}
      <Box sx={{ flexGrow: 1, width: '100%' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            아파트 실거래가 조회
          </Typography>
        </Toolbar>
      </AppBar>
      <AppBar position="static" color="default">
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          indicatorColor="primary" 
          textColor="primary" 
          variant={isMobile ? "scrollable" : "fullWidth"} 
          scrollButtons={isMobile ? "auto" : "false"}
          allowScrollButtonsMobile
        >
          <Tab label="데이터 조회" {...a11yProps(0)} />
          <Tab label="지도 시각화" {...a11yProps(1)} />
          <Tab label="AI 가격 예측" {...a11yProps(2)} />
          <Tab label="AI Q&A" {...a11yProps(3)} />
        </Tabs>
      </AppBar>
      <Container disableGutters sx={{ mb: 4 }}>
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={2} sx={{ mb: 3 }} alignItems="center">
            <Grid item xs={12}> {/* 입력 필드와 버튼을 포함하는 새로운 Grid item */}
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6} md={4} lg={2}>
                  <FormControl fullWidth>
                    <InputLabel>시/도</InputLabel>
                    <Select
                      value={selectedCity}
                      label="시/도"
                      onChange={(e) => setSelectedCity(e.target.value)}
                    >
                      {Object.keys(cities).map((city) => (
                        <MenuItem key={city} value={city}>{city}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={2}>
                  <FormControl fullWidth disabled={!selectedCity}>
                    <InputLabel>시/군/구</InputLabel>
                    <Select
                      value={selectedDistrict}
                      label="시/군/구"
                      onChange={(e) => setSelectedDistrict(e.target.value)}
                    >
                      {districts.map((district) => (
                        <MenuItem key={district} value={district}>{district}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={2}>
                  <TextField
                    fullWidth
                    label="시작년월 (YYYYMM)"
                    value={startYM}
                    onChange={(e) => setStartYM(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={2}>
                  <TextField
                    fullWidth
                    label="종료년월 (YYYYMM)"
                    value={endYM}
                    onChange={(e) => setEndYM(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={2}>
                  <TextField
                    fullWidth
                    label="아파트 이름 (선택 사항)"
                    value={aptName}
                    onChange={(e) => setAptName(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={2}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={handleSearch}
                    disabled={loading || !selectedCity || !selectedDistrict}
                    sx={{ height: '56px' }}
                  >
                    {loading ? <CircularProgress size={24} /> : '데이터 조회'}
                  </Button>
                </Grid>
              </Grid>
            </Grid>
            <Grid item xs={12}> {/* 전용면적 슬라이더를 위한 새로운 Grid item */}
              <Grid container spacing={2}>
                <Grid item xs={6} sm={6} md={6} lg={6} sx={{ mt: 2 }}> {/* mt: 2는 상단 마진을 추가하여 간격 확보 */}
                  <Typography gutterBottom>전용면적 (m²)</Typography>
                  <Slider
                    value={exclusiveAreaRange}
                    onChange={(event, newValue) => setExclusiveAreaRange(newValue)}
                    valueLabelDisplay="auto"
                    min={0}
                    max={200}
                    step={1}
                    marks
                    disableSwap
                  />
                </Grid>
              </Grid>
            </Grid>
          </Grid>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {tradeData.length > 0 ? (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom>월별 평균 거래 가격 추이</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={(function() {
                    const chartData = tradeData.length > 0 ? Object.entries(tradeData.reduce((acc, curr) => {
                      console.log("Processing curr:", curr); // 각 거래 데이터 로그
                      const yearMonth = (curr.deal_year || '') + '-' + String(curr.deal_month || '').padStart(2, '0');
                      const amount = parseNumber(curr.deal_amount);
                      console.log(`YearMonth: ${yearMonth}, Amount: ${amount}`); // 파싱된 금액 로그
                      if (!isNaN(amount)) {
                        if (!acc[yearMonth]) {
                          acc[yearMonth] = { total: 0, count: 0 };
                        }
                        acc[yearMonth].total += amount;
                        acc[yearMonth].count += 1;
                      }
                      console.log("Current accumulator:", acc); // 현재 누적기 로그
                      return acc;
                    }, {})).map(([yearMonth, data]) => ({
                      name: yearMonth,
                      "평균 거래 가격": Math.round(data.total / data.count),
                    })).sort((a, b) => a.name.localeCompare(b.name)) : [];
                    console.log("Final chart data for trade data:", chartData); // 최종 그래프 데이터 로그
                    return chartData;
                  })()}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="평균 거래 가격" stroke="#8884d8" activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          ) : null}

          {tradeData.length > 0 ? (
            <Paper sx={{ width: '100%', overflowX: 'auto', maxHeight: '60vh' }}>
              <TableContainer>
                <Table sx={{ minWidth: 650 }} aria-label="simple table">
                  <TableHead>
                    <TableRow>
                      {Object.keys(tradeData[0])
                        .filter(key => !columnsToExclude.includes(key))
                        .map((key) => (
                          <TableCell key={key}>{columnDisplayNames[key] || key}</TableCell>
                        ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tradeData.map((row, index) => (
                      <TableRow
                        key={index}
                        sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                      >
                        {Object.keys(tradeData[0])
                          .filter(key => !columnsToExclude.includes(key))
                          .map((key, i) => (
                            <TableCell key={i}>{row[key]}</TableCell>
                          ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          ) : (
            !loading && !error && <Typography>조회된 데이터가 없습니다.</Typography>
          )}
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          {geocodedTradeData.length > 0 ? (
            <div ref={mapElement} style={{ width: "100%", height: "500px" }}></div>
          ) : (
            <Typography>조회된 거래 데이터를 기반으로 지도를 표시합니다. VWorld API 키를 'App.jsx' 파일에 설정해주세요.</Typography>
          )}
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ mb: 3 }}>
            <Button
              variant="contained"
              onClick={handleForecast}
              disabled={loading || tradeData.length === 0}
            >
              {loading ? <CircularProgress size={24} /> : '가격 예측 시작'}
            </Button>
          </Box>

          {forecastData && (
            <Box>
              <Typography variant="h6" gutterBottom>가격 예측 그래프</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={(() => {
                    if (!forecastData || !forecastData.historical_data || !forecastData.forecast_data) {
                      return [];
                    }

                    const combinedData = {};

                    forecastData.historical_data.forEach(d => {
                      if (d.ds && d.y !== undefined) {
                        const date = new Date(d.ds);
                        const yearMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                        combinedData[yearMonth] = {
                          name: yearMonth,
                          "실거래가": parseNumber(d.y),
                          "예측 가격": null,
                        };
                      }
                    });

                    forecastData.forecast_data.forEach(d => {
                      if (d.ds && d.yhat !== undefined) {
                        const date = new Date(d.ds);
                        const yearMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                        combinedData[yearMonth] = {
                          name: yearMonth,
                          "실거래가": combinedData[yearMonth] ? combinedData[yearMonth]["실거래가"] : null,
                          "예측 가격": parseNumber(d.yhat),
                        };
                      }
                    });

                    const finalChartData = Object.values(combinedData).sort((a, b) => a.name.localeCompare(b.name));
                    console.log("Final forecast chart data:", finalChartData); // 디버깅 로그 추가
                    return finalChartData;
                  })()}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="실거래가" stroke="#8884d8" activeDot={{ r: 8 }} connectNulls={true} />
                  <Line type="monotone" dataKey="예측 가격" stroke="#82ca9d" connectNulls={true} />
                </LineChart>
              </ResponsiveContainer>

              <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>과거 데이터</Typography>
              <Paper sx={{ width: '100%', overflowX: 'auto', mb: 4 }}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        {Object.keys(forecastData.historical_data[0]).map((key) => (
                          <TableCell key={key}>{key}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {forecastData.historical_data.map((row, index) => (
                        <TableRow key={index}>
                          {Object.values(row).map((value, i) => (
                            <TableCell key={i}>{value}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>

              <Typography variant="h6" gutterBottom>예측 데이터</Typography>
              <Paper sx={{ width: '100%', overflowX: 'auto' }}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        {Object.keys(forecastData.forecast_data[0]).map((key) => (
                          <TableCell key={key}>{key}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {forecastData.forecast_data.map((row, index) => (
                        <TableRow key={index}>
                          {Object.values(row).map((value, i) => (
                            <TableCell key={i}>{value}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Box>
          )}

          {!forecastData && !loading && tradeData.length > 0 && (
            <Typography>가격 예측을 시작하려면 '가격 예측 시작' 버튼을 클릭하세요.</Typography>
          )}
          {!forecastData && !loading && tradeData.length === 0 && (
            <Typography>먼저 데이터를 조회하여 예측할 데이터를 준비해주세요.</Typography>
          )}
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
            <TextField
              fullWidth
              label="질문 입력"
              multiline
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              variant="outlined"
            />
            <Button
              variant="contained"
              onClick={handleChat}
              disabled={loading || tradeData.length === 0 || !question.trim()}
            >
              {loading ? <CircularProgress size={24} /> : '질문하기'}
            </Button>
          </Box>

          {answer && (
            <Box sx={{ mt: 3, p: 2, border: '1px solid #ccc', borderRadius: '4px' }}>
              <Typography variant="h6" gutterBottom>챗봇 답변</Typography>
              <Typography>{answer}</Typography>
            </Box>
          )}

          {!answer && !loading && tradeData.length > 0 && (
            <Typography>챗봇에게 질문을 입력하고 '질문하기' 버튼을 클릭하세요.</Typography>
          )}
          {!answer && !loading && tradeData.length === 0 && (
            <Typography>먼저 데이터를 조회하여 챗봇에게 질문할 데이터를 준비해주세요.</Typography>
          )}
        </TabPanel>
      </Container>
    </Box>
  );
}

export default App
