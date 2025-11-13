<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json; charset=utf-8");

$account = 'ajou9770';
$authKey = '7bfe9eefc98c868431e0c3ca58c534ea37bbea9174a311c90be09636502ee296';
$templateCode = 'ppur_2025111308484413895986979'; // 리조트 신청 템플릿 코드


function getNewToken() {
  global $account, $authKey;
  $credentials = base64_encode("$account:$authKey");

  $ch = curl_init("https://message.ppurio.com/v1/token");
  curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
      "Authorization: Basic $credentials",
      "Content-Type: application/json; charset=utf-8"
    ]
  ]);
  $res = curl_exec($ch);
  curl_close($ch);

  $result = json_decode($res, true);
  if (isset($result['token'])) {
    file_put_contents(__DIR__ . '/token.json', json_encode(['token' => $result['token']]));
    return $result['token'];
  }
  return false;
}

function loadToken() {
  $file = __DIR__ . '/token.json';
  if (!file_exists($file)) return getNewToken();
  $saved = json_decode(file_get_contents($file), true);
  return $saved['token'] ?? getNewToken();
}

function formatPhone($num) {
  return preg_replace('/[^0-9]/', '', $num);
}

// ====== GAS에서 오는 JSON ======
$input = json_decode(file_get_contents("php://input"), true);
$name = $input['name'] ?? '';
$to   = $input['to'] ?? '';
$var1 = $input['var1'] ?? ''; // 리조트명
$var2 = $input['var2'] ?? ''; // 접수정보(일시 + 인원)
$var3 = $input['var3'] ?? ''; // 당첨확률 텍스트

if (!$name || !$to || !$var1 || !$var2 || !$var3) {
  echo json_encode(["code" => "9000", "description" => "❌ 필수 입력 누락"]);
  exit;
}

$targets = [[
  "to" => formatPhone($to),
  "name" => $name,  // ✅ 여기서 템플릿의 #{name}으로 매핑됨
  "changeWord" => [
    "var1" => $var1,
    "var2" => $var2,
    "var3" => $var3
  ]
]];

function sendAlimtalk($token, $targets) {
  global $account, $templateCode;
  $payload = [
    "account" => $account,
    "messageType" => "ALT",
    "senderProfile" => "@아주대의료원신협",
    "templateCode" => $templateCode,
    "duplicateFlag" => "Y",
    "isResend" => "N",
    "targetCount" => count($targets),
    "targets" => $targets,
    "refKey" => "resort_" . time()
  ];

  $ch = curl_init("https://message.ppurio.com/v1/kakao");
  curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
      "Authorization: Bearer $token",
      "Content-Type: application/json; charset=utf-8"
    ],
    CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE)
  ]);
  $res = curl_exec($ch);
  curl_close($ch);
  return $res;
}

$token = loadToken();
$response = sendAlimtalk($token, $targets);

// 토큰 만료 시 재발급 & 재전송
if (strpos($response, 'jwt expired') !== false || strpos($response, 'Token issue failed') !== false) {
  $token = getNewToken();
  $response = sendAlimtalk($token, $targets);
}

echo $response;
?>
