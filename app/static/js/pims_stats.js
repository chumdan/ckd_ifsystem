/**
 * PIMS 배치요약 통계 기능 JavaScript
 * 기본 조회 기능은 pims.js를 재사용하고, 통계 기능만 추가
 */

// ========================================
// 1. 통계 전용 API URL 및 변수
// ========================================

// 통계 API 기본 URL (충돌 방지)
const STATS_API_BASE_URL = '/api/pims-stats';

// 통계 DataTables 객체
let pimsStatsTable = null;

// Plotly 차트 변수들
let currentChartData = null;  // 현재 차트 데이터 저장

// ========================================
// 2. 페이지 로드 완료 후 통계 기능 초기화
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('PIMS 배치요약 통계 기능이 로드되었습니다.');
    
    // 기존 pims.js의 searchPimsData 함수를 통계용으로 오버라이드
    overrideSearchFunction();
});

// ========================================
// 3. 기존 함수 오버라이드
// ========================================
function overrideSearchFunction() {
    // 기존 searchPimsData 함수를 통계용으로 교체
    window.searchPimsData = function() {
        console.log('🔄 통계용 searchPimsData 함수가 호출되었습니다.');
        searchStatsData();
    };
    
    // 기존 시간 설정 함수들을 통계 페이지 ID에 맞게 오버라이드
    window.showMultipleTimeSection = function(batches) {
        console.log('🔄 통계용 showMultipleTimeSection 호출:', batches);
        showStatsMultipleTimeSection(batches);
    };
    
    window.showSingleTimeSection = function() {
        console.log('🔄 통계용 showSingleTimeSection 호출');
        showStatsSingleTimeSection();
    };
    
    window.updateBatchTimeContainer = function(batches) {
        console.log('🔄 통계용 updateBatchTimeContainer 호출:', batches);
        updateStatsBatchTimeContainer(batches);
    };
    
    console.log('✅ 모든 함수가 통계용으로 오버라이드되었습니다.');
}



// ========================================
// 3. 통계 페이지 전용 시간 설정 함수들
// ========================================

/**
 * 통계 페이지용 단일 시간 설정 섹션 표시
 */
function showStatsSingleTimeSection() {
    console.log('통계 페이지: 단일 시간 설정 모드로 전환');
    
    const singleSection = document.getElementById('singleTimeSection1');
    const multipleSection = document.getElementById('multipleTimeSection1');
    
    if (singleSection) singleSection.classList.remove('d-none');
    if (multipleSection) multipleSection.classList.add('d-none');
    
    // 배치별 시간 컨테이너 초기화
    clearStatsBatchTimeContainer();
}

/**
 * 통계 페이지용 배치별 개별 시간 설정 섹션 표시
 */
function showStatsMultipleTimeSection(batches) {
    console.log('통계 페이지: 배치별 개별 시간 설정 모드로 전환:', batches);
    
    const singleSection = document.getElementById('singleTimeSection1');
    const multipleSection = document.getElementById('multipleTimeSection1');
    
    if (singleSection) singleSection.classList.add('d-none');
    if (multipleSection) multipleSection.classList.remove('d-none');
    
    // 단일 시간 필드들 초기화
    const startTime1 = document.getElementById('startTime1');
    const endTime1 = document.getElementById('endTime1');
    if (startTime1) startTime1.value = '';
    if (endTime1) endTime1.value = '';
    
    // 배치별 시간 필드 생성
    updateStatsBatchTimeContainer(batches);
}

/**
 * 통계 페이지용 배치별 시간 컨테이너 업데이트
 */
function updateStatsBatchTimeContainer(batches) {
    console.log('통계 페이지: 배치별 개별 시간 필드 업데이트:', batches);
    
    const container = document.getElementById('batchTimeContainer1');
    if (!container) return;
    
    // 기존 필드들 제거
    container.innerHTML = '';
    
    // 배치별 시간 필드 생성
    batches.forEach(batch => {
        if (batch && batch.trim() !== '') {
            const batchCard = createStatsBatchTimeCard(batch);
            container.appendChild(batchCard);
        }
    });
    
    // 배치가 하나도 없으면 안내 메시지 표시
    if (batches.length === 0) {
        clearStatsBatchTimeContainer();
    }
}

/**
 * 통계 페이지용 개별 배치 시간 설정 카드 생성
 */
function createStatsBatchTimeCard(batchNo) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'batch-time-card mb-3';
    cardDiv.setAttribute('data-batch', batchNo);
    
    cardDiv.innerHTML = `
        <div class="card">
            <div class="card-header bg-light">
                <h6 class="mb-0">
                    <span class="badge bg-primary">${batchNo}</span>
                    배치별 시간 설정
                </h6>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    <div class="col-md-6">
                        <label for="batchStart_${batchNo}" class="form-label">
                            <i class="fas fa-play me-1"></i>
                            시작시간
                        </label>
                        <input type="datetime-local" 
                               class="form-control time-input" 
                               id="batchStart_${batchNo}" 
                               name="batch_start_${batchNo}">
                        <div class="form-text">${batchNo} 배치 시작시간</div>
                    </div>
                    <div class="col-md-6">
                        <label for="batchEnd_${batchNo}" class="form-label">
                            <i class="fas fa-stop me-1"></i>
                            종료시간
                        </label>
                        <input type="datetime-local" 
                               class="form-control time-input" 
                               id="batchEnd_${batchNo}" 
                               name="batch_end_${batchNo}">
                        <div class="form-text">${batchNo} 배치 종료시간</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return cardDiv;
}

/**
 * 통계 페이지용 배치별 시간 설정 컨테이너 초기화
 */
function clearStatsBatchTimeContainer() {
    const container = document.getElementById('batchTimeContainer1');
    if (container) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="fas fa-info-circle me-2"></i>
                배치를 선택하면 각 배치별 시간 설정이 가능합니다.
            </div>
        `;
    }
}

// ========================================
// 4. 통계 데이터 조회 메인 함수
// ========================================
function searchStatsData() {
    console.log('통계 데이터 조회를 시작합니다.');
    
    // 폼 데이터 수집 (기존 pims.js의 검증 로직 재사용)
    const formData = collectStatsFormData();
    
    if (!formData) {
        console.log('폼 검증 실패');
        return;
    }
    
    console.log('수집된 통계 조회 데이터:', formData);
    
    // 제품 타입 별도 확인 (formData에서 제거되었으므로)
    const productType = document.getElementById('productType1').value;
    
    // 로딩 상태 표시
    showStatsLoading(true);
    
    // 제품 타입에 따라 적절한 통계 API 호출
    if (productType === 'basic') {
        searchStatsBasic(formData);
    } else if (productType === 'l23') {
        searchStatsL23(formData);
    } else {
        showAlert('지원하지 않는 제품 타입입니다.', 'danger');
        showStatsLoading(false);
    }
}

// ========================================
// 5. 통계 API 호출 함수들
// ========================================

/**
 * 기존 고형 통계 API 호출
 */
function searchStatsBasic(formData) {
    console.log('기존 고형 통계 조회 시작:', formData);
    
    fetch(`${STATS_API_BASE_URL}/get-stats-basic`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('기존 고형 통계 조회 성공:', data);
        handleStatsResponse(data);
    })
    .catch(error => {
        console.error('기존 고형 통계 조회 오류:', error);
        showAlert('통계 조회 중 오류가 발생했습니다.', 'danger');
        showStatsLoading(false);
    });
}

/**
 * 스마트 고형 통계 API 호출
 */
function searchStatsL23(formData) {
    console.log('스마트 고형 통계 조회 시작:', formData);
    
    fetch(`${STATS_API_BASE_URL}/get-stats-l23`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('스마트 고형 통계 조회 성공:', data);
        handleStatsResponse(data);
    })
    .catch(error => {
        console.error('스마트 고형 통계 조회 오류:', error);
        showAlert('통계 조회 중 오류가 발생했습니다.', 'danger');
        showStatsLoading(false);
    });
}

// ========================================
// 6. 통계 응답 처리 및 표시
// ========================================

/**
 * 통계 API 응답 처리
 */
function handleStatsResponse(data) {
    showStatsLoading(false);
    
    if (data.success && data.data && data.data.length > 0) {
        console.log('통계 데이터 표시:', data.data.length, '행');
        
        // 📊 데이터 캐싱 (차트용 재사용)
        currentStatsData = data.data;
        currentFormData = collectStatsFormData();
        console.log('✅ 통계 데이터 캐싱 완료 - 차트 생성 시 재조회 없음');
        
        displayStatsData(data.data);
        showStatsInfo(data.data.length);
    } else {
        console.log('통계 데이터 없음:', data.message || '데이터가 없습니다.');
        showAlert(data.message || '조회된 통계 데이터가 없습니다.', 'warning');
    }
}

/**
 * 통계 데이터를 테이블에 표시 (기존 PIMS와 동일한 구조)
 */
function displayStatsData(data) {
    console.log('통계 테이블을 생성합니다. 데이터 수:', data.length);
    
    // 기존 테이블 제거 (안전하게)
    if (pimsStatsTable && typeof pimsStatsTable.destroy === 'function') {
        try {
            pimsStatsTable.destroy();
        } catch (e) {
            console.warn('기존 테이블 제거 중 오류:', e);
        }
        pimsStatsTable = null;
    }
    
    // 결과 컨테이너 표시
    document.getElementById('resultContainerStats').style.display = 'block';
    
    // 기존 PIMS와 동일한 테이블 HTML 생성 (테이블 오른쪽 상단에 다운로드 버튼)
    const tableHtml = `
        <div class="card shadow-ckd">
            <div class="card-header result-header d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-0">
                        <i class="fas fa-chart-bar me-2"></i>
                        📊 PIMS 배치요약 결과 (${data.length}개 배치)
                        <small class="text-muted ms-3">
                            <i class="fas fa-info-circle me-1"></i>
                            대량 데이터를 통계량으로 압축한 결과입니다
                        </small>
                    </h6>
                </div>
                <div>
                    <button type="button" 
                            class="btn btn-outline-success btn-sm" 
                            id="downloadStatsCsvBtn"
                            title="통계 데이터를 CSV 파일로 다운로드">
                        <i class="fas fa-download me-2"></i>
                        CSV 다운로드
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table id="pimsStatsTable" class="table table-striped table-hover stats-table">
                        <thead class="table-dark">
                            <!-- 테이블 헤더는 동적으로 생성 -->
                        </thead>
                        <tbody>
                            <!-- 테이블 내용은 DataTables가 자동 생성 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // 테이블 컨테이너에 HTML 추가
    document.getElementById('statsTableContainer').innerHTML = tableHtml;
    
    // 컬럼 정의 생성
    const columns = createStatsColumns(data[0]);
    
    // DataTables 초기화 (jQuery 확인 후)
    if (typeof $ === 'undefined') {
        console.error('jQuery가 로드되지 않았습니다!');
        return;
    }
    
    pimsStatsTable = $('#pimsStatsTable').DataTable({
        data: data,
        columns: columns,
        responsive: false,          // 반응형 테이블 비활성화 (한 줄 표시를 위해)
        scrollX: true,             // 가로 스크롤 활성화
        autoWidth: false,          // 자동 폭 조정 비활성화
        language: {
            "lengthMenu": "_MENU_ 개씩 보기",
            "search": "검색:",
            "info": "_TOTAL_개 중 _START_~_END_ 표시",
            "infoEmpty": "데이터 없음",
            "infoFiltered": "(_MAX_개에서 필터링)",
            "paginate": {
                "first": "첫페이지",
                "last": "마지막",
                "next": "다음",
                "previous": "이전"
            },
            "emptyTable": "표시할 데이터가 없습니다.",
            "zeroRecords": "검색 결과가 없습니다."
        },
        pageLength: 25,
        order: [[0, 'asc']], // 첫 번째 컬럼 기준 정렬
        columnDefs: [              // 모든 컬럼에 대한 설정
            {
                targets: '_all',   // 모든 컬럼에 적용
                className: 'dt-nowrap text-center', // 줄바꿈 방지 + 가운데 정렬
                render: function(data, type, row) {
                    if (type === 'display' && data != null) {
                        return '<span style="white-space: nowrap !important; word-wrap: normal !important; word-break: keep-all !important;">' + data + '</span>';
                    }
                    return data;
                }
            }
        ],
        createdRow: function(row, data, index) {
            // 생성된 행의 모든 셀에 강제로 nowrap 적용 (기존 PIMS와 동일)
            $(row).find('td').css({
                'white-space': 'nowrap !important',
                'word-wrap': 'normal !important',
                'word-break': 'keep-all !important',
                'text-overflow': 'clip !important',
                'overflow': 'visible !important'
            });
            
            // 헤더도 강제 적용
            $(row).closest('table').find('th').css({
                'white-space': 'nowrap !important',
                'word-wrap': 'normal !important',
                'word-break': 'keep-all !important'
            });
        },
        drawCallback: function(settings) {
            // 테이블이 그려질 때마다 강제로 스타일 적용
            $('#pimsStatsTable th, #pimsStatsTable td').css({
                'white-space': 'nowrap !important',
                'word-wrap': 'normal !important',
                'word-break': 'keep-all !important',
                'text-overflow': 'clip !important',
                'overflow': 'visible !important'
            });
        }
    });
    
    console.log('통계 테이블 생성 완료');
    
    // CSV 다운로드 버튼 이벤트 리스너 추가 (기존 PIMS와 동일)
    const downloadBtn = document.getElementById('downloadStatsCsvBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            console.log('통계 CSV 다운로드 버튼 클릭됨');
            downloadAllStatsDataAsCSV();
        });
    }
    
    // 차트 분석 영역 표시 및 초기화
    showChartAnalysis(data);
}

/**
 * 통계 데이터 컬럼 정의 생성 (배치번호를 첫 번째 컬럼으로)
 */
function createStatsColumns(sampleRow) {
    const columns = [];
    
    // 1. 배치번호를 첫 번째 컬럼으로 고정
    if (sampleRow.hasOwnProperty('배치번호')) {
        columns.push({
            title: '배치번호',
            data: '배치번호',
            className: 'text-center fw-bold',
            width: '120px'
        });
    }
    
    // 2. 품목코드, 공정코드를 다음 컬럼으로
    const priorityColumns = ['품목코드', '공정코드'];
    for (const colName of priorityColumns) {
        if (sampleRow.hasOwnProperty(colName)) {
            columns.push({
                title: colName,
                data: colName,
                className: 'text-center',
                width: '100px'
            });
        }
    }
    
    // 3. 나머지 컬럼들 추가 (배치번호, 품목코드, 공정코드 제외)
    const excludeColumns = ['배치번호', '품목코드', '공정코드'];
    for (const key in sampleRow) {
        if (!excludeColumns.includes(key)) {
            columns.push({
                title: key,
                data: key,
                className: 'text-center'
            });
        }
    }
    
    return columns;
}

// ========================================
// 7. 유틸리티 함수들
// ========================================

/**
 * 통계 조회용 폼 데이터 수집
 * 기존 pims.js의 collectTimeData() 재사용
 */
function collectStatsFormData() {
    // 기본 필드 값들 수집
    const productType = document.getElementById('productType1').value;
    const itemCode = document.getElementById('itemCode1').value.trim();
    const batchSelect = document.getElementById('batchSelect1');
    const processSelect = document.getElementById('processSelect1');
    
    // 필수 값 검증
    if (!productType) {
        showAlert('제품 타입을 선택해주세요.', 'warning');
        return null;
    }
    
    if (!itemCode) {
        showAlert('품목코드를 입력해주세요.', 'warning');
        return null;
    }
    
    if (!batchSelect.value) {
        showAlert('배치를 선택해주세요.', 'warning');
        return null;
    }
    
    if (!processSelect.value) {
        showAlert('공정을 선택해주세요.', 'warning');
        return null;
    }
    
    // 선택된 배치들 수집
    const selectedBatches = Array.from(batchSelect.selectedOptions)
        .map(option => option.value)
        .filter(value => value !== "");
    
    // 시간 데이터 수집 (통계 페이지 전용)
    const timeData = collectStatsTimeData();
    
    // 백엔드 API 형식에 맞게 데이터 구조 생성
    const apiData = {
        itemcode: itemCode,
        batch_no: selectedBatches.join(','),  // 배열 → 쉼표로 구분된 문자열
        proc_code: processSelect.value,
        mode: timeData.mode,  // "common" 또는 "individual"
    };
    
    // 시간 데이터 추가 (모드에 따라)
    if (timeData.mode === 'individual') {
        apiData.batch_time_ranges = timeData.batch_time_ranges;
    } else {
        apiData.start_time = timeData.start_time || "";
        apiData.end_time = timeData.end_time || "";
    }
    
    console.log('📤 백엔드로 전송할 데이터:', apiData);
    
    return apiData;
}

/**
 * 통계 페이지 전용 시간 데이터 수집
 * pims.js의 collectTimeData와 유사하지만 통계 페이지 ID 사용
 */
function collectStatsTimeData() {
    // 통계 페이지의 ID들 사용
    const multipleTimeSection = document.getElementById('multipleTimeSection1');
    const isMultipleMode = multipleTimeSection && !multipleTimeSection.classList.contains('d-none');
    
    if (isMultipleMode) {
        // 배치별 개별 시간 모드
        const batchTimeRanges = {};
        const batchCards = document.querySelectorAll('.batch-time-card');
        
        batchCards.forEach(card => {
            const batchNo = card.getAttribute('data-batch');
            const startTimeInput = document.getElementById(`batchStart_${batchNo}`);
            const endTimeInput = document.getElementById(`batchEnd_${batchNo}`);
            
            if (startTimeInput || endTimeInput) {
                batchTimeRanges[batchNo] = {
                    start: startTimeInput ? startTimeInput.value || null : null,
                    end: endTimeInput ? endTimeInput.value || null : null
                };
            }
        });
        
        return {
            mode: 'individual',
            batch_time_ranges: batchTimeRanges
        };
        
    } else {
        // 단일/공통 시간 모드 (통계 페이지 ID 사용)
        const startTimeInput = document.getElementById('startTime1');
        const endTimeInput = document.getElementById('endTime1');
        
        return {
            mode: 'common',
            start_time: startTimeInput ? startTimeInput.value || null : null,
            end_time: endTimeInput ? endTimeInput.value || null : null
        };
    }
}

/**
 * 통계 정보 표시 (배치별)
 */
function showStatsInfo(dataCount) {
    console.log(`통계 정보 표시: ${dataCount}개 배치`);
    // 기존 PIMS와 동일한 구조로 테이블 헤더에 정보가 포함되므로 별도 처리 불필요
}

/**
 * 통계 로딩 상태 표시
 */
function showStatsLoading(show) {
    const searchBtn = document.getElementById('searchBtnStats');
    
    if (searchBtn) {
        if (show) {
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> 통계 처리 중...';
        } else {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-chart-line me-1"></i> 통계 조회';
        }
    }
}

// ========================================
// 8. 통계 데이터 CSV 다운로드 함수들 (기존 PIMS와 동일한 로직)
// ========================================

/**
 * 현재 표시된 통계 데이터를 CSV로 다운로드
 * 기존 PIMS와 동일한 로직이지만 통계 데이터에 특화
 */
function downloadAllStatsDataAsCSV() {
    console.log('통계 CSV 다운로드를 시작합니다...');
    
    // 다운로드 버튼 비활성화 및 로딩 표시
    const downloadBtn = document.getElementById('downloadStatsCsvBtn');
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>다운로드 중...';
    
    // 현재 테이블에 표시된 통계 데이터 가져오기
    const statsData = pimsStatsTable.data().toArray();
    
    if (!statsData || statsData.length === 0) {
        showAlert('다운로드할 통계 데이터가 없습니다.', 'warning');
        resetStatsDownloadButton();
        return;
    }
    
    console.log(`통계 다운로드용 데이터: ${statsData.length}건`);
    
    // 폼 데이터 수집 (파일명 생성용)
    const formData = {
        itemcode: document.getElementById('itemCode1').value.trim(),
        batch_no: Array.from(document.getElementById('batchSelect1').selectedOptions)
                       .map(option => option.value)
                       .filter(value => value !== "")
                       .join(','),
        proc_code: document.getElementById('processSelect1').value,
        product_type: document.getElementById('productType1').value
    };
    
    // CSV 파일 생성 및 다운로드
    try {
        generateAndDownloadStatsCSV(statsData, formData);
        showAlert(`통계 CSV 다운로드 완료! ${statsData.length}개 배치의 통계 데이터를 다운로드했습니다.`, 'success');
    } catch (error) {
        console.error('통계 CSV 다운로드 오류:', error);
        showAlert('CSV 다운로드 중 오류가 발생했습니다.', 'danger');
    }
    
    // 다운로드 버튼 복원
    resetStatsDownloadButton();
}

/**
 * 통계 데이터를 CSV 파일로 생성 및 다운로드
 * 기존 PIMS의 generateAndDownloadCSV와 동일한 로직
 */
function generateAndDownloadStatsCSV(data, formData) {
    console.log('통계 CSV 파일을 생성합니다...');
    
    if (!data || data.length === 0) {
        console.log('CSV 생성할 통계 데이터가 없습니다.');
        return;
    }
    
    // CSV 헤더 생성 (중요한 기본 정보를 맨 앞에 배치)
    const headers = createOrderedStatsHeaders(data[0]);
    let csvContent = headers.join(',') + '\n';
    
    // CSV 데이터 생성 (숫자 데이터 소수점 처리)
    data.forEach(row => {
        const values = headers.map(header => {
            let value = row[header];
            
            // null, undefined 처리
            if (value === null || value === undefined) {
                return '';
            }
            
            // 숫자 데이터 처리 (소수점 4째자리 반올림)
            if (typeof value === 'number' && value % 1 !== 0) {
                value = parseFloat(value.toFixed(4));
            }
            
            // 시간 데이터 포맷 변경 (T 제거)
            if (typeof value === 'string' && value.includes('T')) {
                value = value.replace('T', ' ').split('.')[0];
            }
            
            // CSV에서 쉼표가 포함된 텍스트는 따옴표로 감싸기
            if (typeof value === 'string' && (value.includes(',') || value.includes('\n') || value.includes('"'))) {
                value = '"' + value.replace(/"/g, '""') + '"';
            }
            
            return value;
        });
        
        csvContent += values.join(',') + '\n';
    });
    
    // 파일명 생성 (현재 날짜 포함, 통계 전용)
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
    const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, ''); // HHMMSS
    const productTypeStr = formData.product_type === 'basic' ? '기존고형' : '스마트고형';
    const fileName = `PIMS_통계요약_${productTypeStr}_${formData.itemcode}_${formData.proc_code}_${dateStr}_${timeStr}.csv`;
    
    // CSV 파일 다운로드 실행
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' }); // BOM 추가 (Excel 한글 지원)
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', fileName);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        console.log(`통계 CSV 파일 다운로드 완료: ${fileName}`);
    } else {
        console.error('브라우저에서 파일 다운로드를 지원하지 않습니다.');
        showAlert('브라우저에서 파일 다운로드를 지원하지 않습니다.', 'danger');
    }
}

/**
 * 통계 다운로드 버튼을 원래 상태로 복원
 */
function resetStatsDownloadButton() {
    const downloadBtn = document.getElementById('downloadStatsCsvBtn');
    if (downloadBtn) {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>CSV 다운로드';
    }
}

/**
 * CSV 다운로드용 컬럼 순서 정렬 (기본 정보를 맨 앞에 배치)
 * @param {Object} sampleRow - 첫 번째 데이터 행
 * @returns {Array} 정렬된 헤더 배열
 */
function createOrderedStatsHeaders(sampleRow) {
    const orderedHeaders = [];
    
    // 1. 가장 중요한 기본 정보들을 맨 앞에 배치
    const priorityColumns = [
        '처리일시',     // 처리 시간
        '배치번호',     // 배치 식별
        '품목코드',     // 제품 식별  
        '공정코드',     // 공정 식별
        '시작시간',     // 시간 범위
        '종료시간'      // 시간 범위
    ];
    
    // 우선순위 컬럼들 추가 (실제로 존재하는 것만)
    for (const colName of priorityColumns) {
        if (sampleRow.hasOwnProperty(colName)) {
            orderedHeaders.push(colName);
        }
    }
    
    // 2. 통계 데이터들을 그 다음에 배치 (변수명_통계량 형태)
    const statsColumns = [];
    const basicColumns = [];
    
    for (const key in sampleRow) {
        // 이미 추가된 우선순위 컬럼은 제외
        if (priorityColumns.includes(key)) {
            continue;
        }
        
        // 통계량 패턴 (_평균, _표준편차, _25%, _50%, _75%)
        if (key.includes('_평균') || key.includes('_표준편차') || 
            key.includes('_25%') || key.includes('_50%') || key.includes('_75%')) {
            statsColumns.push(key);
        } else {
            // 기타 기본 컬럼들
            basicColumns.push(key);
        }
    }
    
    // 3. 통계 컬럼들을 변수명별로 그룹화하여 정렬
    statsColumns.sort((a, b) => {
        // 변수명 추출 (예: "L23_2526_ROOM_온도_평균" → "L23_2526_ROOM_온도")
        const getVariableName = (colName) => {
            const parts = colName.split('_');
            if (parts.length >= 2) {
                return parts.slice(0, -1).join('_'); // 마지막 통계량 부분 제거
            }
            return colName;
        };
        
        const varA = getVariableName(a);
        const varB = getVariableName(b);
        
        // 변수명으로 먼저 정렬
        if (varA !== varB) {
            return varA.localeCompare(varB);
        }
        
        // 같은 변수명이면 통계량 순서로 정렬 (평균, 표준편차, 25%, 50%, 75%)
        const statOrder = ['평균', '표준편차', '25%', '50%', '75%'];
        const getStatOrder = (colName) => {
            for (let i = 0; i < statOrder.length; i++) {
                if (colName.includes('_' + statOrder[i])) {
                    return i;
                }
            }
            return 999;
        };
        
        return getStatOrder(a) - getStatOrder(b);
    });
    
    // 4. 최종 헤더 순서: 기본정보 → 기타기본컬럼 → 통계데이터
    return [...orderedHeaders, ...basicColumns, ...statsColumns];
}

// ========================================
// 8. 차트 분석 기능 (Python 백엔드 활용)
// ========================================

// 차트 전역 변수들 (기존에 선언된 변수 재사용)

/**
 * 차트 분석 영역 표시 및 초기화
 */
function showChartAnalysis(statsData) {
    console.log('차트 분석 영역을 표시합니다.');
    
    // 차트 분석 영역 표시 (HTML ID와 매칭)
    const chartSection = document.getElementById('chartAnalysisContainer');
    if (chartSection) {
        chartSection.style.display = 'block';
        
        // 차트 생성 버튼 추가 (테이블 아래)
        addChartButton();
    }
}

/**
 * 차트 생성 버튼을 테이블 아래에 추가
 */
function addChartButton() {
    // 기존 버튼이 있으면 제거
    const existingBtn = document.getElementById('chartGenerateBtn');
    if (existingBtn) {
        existingBtn.remove();
    }
    
    // 차트 생성 버튼 HTML
    const buttonHtml = `
        <div class="d-flex justify-content-end mt-3 mb-3" id="chartButtonContainer">
            <button type="button" 
                    class="btn btn-info btn-sm" 
                    id="chartGenerateBtn"
                    style="padding: 8px 16px;">
                <i class="fas fa-chart-line me-2"></i>
                차트 분석
                <small class="ms-2" style="font-size: 10px; opacity: 0.8;">
                    <i class="fas fa-bolt"></i> 빠른처리
                </small>
            </button>
        </div>
    `;
    
    // 테이블 컨테이너 뒤에 버튼 추가
    const tableContainer = document.getElementById('statsTableContainer');
    if (tableContainer) {
        tableContainer.insertAdjacentHTML('afterend', buttonHtml);
        
        // 버튼 이벤트 리스너 추가
        const chartBtn = document.getElementById('chartGenerateBtn');
        if (chartBtn) {
            chartBtn.addEventListener('click', generateChartsFromCachedData);
        }
    }
}

/**
 * 캐싱된 데이터로 차트 생성 (재조회 없음)
 */
function generateChartsFromCachedData() {
    console.log('📊 캐싱된 데이터로 차트 생성 시작...');
    
    if (!currentStatsData || !currentFormData) {
        showAlert('먼저 통계 데이터를 조회해주세요.', 'warning');
        return;
    }
    
    try {
        // 로딩 표시
        showChartLoading(true);
        
        // 캐싱된 통계 데이터에서 차트 데이터 생성
        const chartData = generateChartDataFromStats(currentStatsData);
        
        if (chartData) {
            currentChartData = chartData;
            console.log('✅ 차트 데이터 생성 성공:', currentChartData);
            
            // 차트 렌더링
            renderTrendChart();
            renderCvChart();
            
            // 로딩 숨기기 및 차트 영역 표시
            showChartLoading(false);
            showChartContainer(true);
            
            showAlert(`차트 생성 완료! ${chartData.variables.length}개 변수 분석`, 'success');
            
        } else {
            throw new Error('차트 데이터 생성 실패');
        }
        
    } catch (error) {
        console.error('❌ 차트 생성 중 오류:', error);
        showAlert('차트 생성 중 오류가 발생했습니다.', 'danger');
        showChartLoading(false);
    }
}

/**
 * 통계 데이터에서 차트 데이터 생성 (JavaScript에서 처리)
 */
function generateChartDataFromStats(statsData) {
    console.log('📈 통계 데이터에서 차트 데이터 생성...');
    
    if (!statsData || statsData.length === 0) {
        console.error('통계 데이터가 없습니다.');
        return null;
    }
    
    // 변수 목록 추출 (평균값 컬럼들)
    const sampleRow = statsData[0];
    const variables = [];
    const trendData = {};
    const cvData = [];
    
    // 평균, 표준편차 컬럼 찾기
    for (const key in sampleRow) {
        if (key.includes('_평균')) {
            const varName = key.replace('_평균', '');
            variables.push(varName);
            
            // 트렌드 데이터 생성 (배치별 평균값)
            trendData[varName] = statsData.map(row => ({
                batch: row['배치번호'] || row['batch_no'] || 'Unknown',
                value: parseFloat(row[key]) || 0
            }));
            
            // CV 데이터 생성 (변동계수 = 표준편차/평균 * 100)
            const stdKey = key.replace('_평균', '_표준편차');
            if (sampleRow.hasOwnProperty(stdKey)) {
                const avgValues = statsData.map(row => parseFloat(row[key]) || 0);
                const stdValues = statsData.map(row => parseFloat(row[stdKey]) || 0);
                
                // 전체 평균과 평균 표준편차로 CV 계산
                const totalAvg = avgValues.reduce((a, b) => a + b, 0) / avgValues.length;
                const totalStd = stdValues.reduce((a, b) => a + b, 0) / stdValues.length;
                const cv = totalAvg !== 0 ? (totalStd / totalAvg) * 100 : 0;
                
                cvData.push({
                    variable: varName,
                    cv: cv
                });
            }
        }
    }
    
    console.log(`📊 차트 데이터 생성 완료: ${variables.length}개 변수, ${statsData.length}개 배치`);
    
    return {
        variables: variables,
        trend_data: trendData,
        cv_data: cvData,
        summary: {
            total_variables: variables.length,
            total_batches: statsData.length
        }
    };
}

/**
 * 차트 데이터 로드 (Python 백엔드에서 모든 계산 처리) - DEPRECATED
 */
async function loadChartData() {
    console.log('📊 차트 데이터 로드 시작...');
    
    // 현재 조회된 통계 데이터가 있는지 확인
    if (!pimsStatsTable || pimsStatsTable.data().length === 0) {
        showAlert('먼저 통계 데이터를 조회해주세요.', 'warning');
        return;
    }
    
    // 현재 폼 데이터 수집
    const formData = collectStatsFormData();
    
    if (!formData.itemcode || !formData.batch_no || !formData.proc_code) {
        showAlert('품목코드, 배치번호, 공정코드를 모두 입력해주세요.', 'warning');
        return;
    }
    
    try {
        // 로딩 표시
        showChartLoading(true);
        
        // 제품 타입 추가 (Python API에서 필요)
        const chartRequestData = {
            ...formData,
            product_type: document.querySelector('input[name="productType"]:checked')?.value || 'basic'
        };
        
        console.log('📡 차트 데이터 API 호출:', chartRequestData);
        
        // Python 백엔드에서 차트 데이터 생성
        const response = await fetch('/api/pims-stats/get-chart-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(chartRequestData)
        });
        
        const result = await response.json();
        
        if (result.success && result.data) {
            currentChartData = result.data;
            console.log('✅ 차트 데이터 로드 성공:', currentChartData);
            
            // 차트 렌더링
            renderTrendChart();
            renderCvChart();
            
            // 로딩 숨기기 및 차트 영역 표시
            showChartLoading(false);
            showChartContainer(true);
            
            showAlert(`차트 생성 완료! ${currentChartData.summary.total_variables}개 변수, ${currentChartData.summary.total_batches}개 배치`, 'success');
            
        } else {
            console.error('❌ 차트 데이터 로드 실패:', result.message);
            showAlert(`차트 데이터 로드 실패: ${result.message}`, 'danger');
            showChartLoading(false);
        }
        
    } catch (error) {
        console.error('❌ 차트 데이터 로드 중 오류:', error);
        showAlert('차트 데이터 로드 중 오류가 발생했습니다.', 'danger');
        showChartLoading(false);
    }
}

/**
 * 트렌드 차트 렌더링 (Plotly 사용)
 */
function renderTrendChart() {
    if (!currentChartData || !currentChartData.variables.length) {
        console.warn('⚠️ 트렌드 차트 데이터가 없습니다.');
        return;
    }
    
    // 변수 드롭다운 업데이트
    updateVariableDropdown();
    
    // 첫 번째 변수로 초기화
    const firstVariable = currentChartData.variables[0];
    updateTrendChart(firstVariable);
}

/**
 * 트렌드 차트 업데이트 (변수 선택 시) - Plotly 버전
 */
function updateTrendChart(selectedVariable) {
    const chartDiv = document.getElementById('trendChart');
    if (!chartDiv) {
        console.error('트렌드 차트 영역을 찾을 수 없습니다.');
        return;
    }
    
    if (!currentChartData.trend_data[selectedVariable]) {
        console.warn(`⚠️ ${selectedVariable} 변수의 트렌드 데이터가 없습니다.`);
        return;
    }
    
    const trendData = currentChartData.trend_data[selectedVariable];
    
    // 📊 Plotly 데이터 준비
    const plotData = [{
        x: trendData.map(d => d.batch),
        y: trendData.map(d => d.value),
        type: 'scatter',
        mode: 'lines+markers',
        name: `${selectedVariable} 평균값`,
        line: {
            color: '#007bff',
            width: 3,
            shape: 'spline'  // 부드러운 곡선
        },
        marker: {
            color: '#007bff',
            size: 6,
            line: {
                color: '#ffffff',
                width: 1
            }
        },
        fill: 'tonexty',
        fillcolor: 'rgba(0, 123, 255, 0.1)'
    }];
    
    // 📊 Plotly 레이아웃 설정
    const layout = {
        title: {
            text: `${selectedVariable} 배치별 트렌드`,
            font: { size: 14, color: '#333' }
        },
        xaxis: {
            title: '배치번호',
            tickangle: -90,  // X축 틱을 90도로 회전
            automargin: true,  // 자동 마진 조정
            showgrid: true,
            gridcolor: '#e6e6e6'
        },
        yaxis: {
            title: '평균값',
            automargin: true,  // 자동 마진 조정
            showgrid: true,
            gridcolor: '#e6e6e6'
        },
        autosize: true,  // 컨테이너 크기에 자동 맞춤
        showlegend: false,
        plot_bgcolor: '#fafafa',
        paper_bgcolor: '#ffffff'
    };
    
    // 📊 Plotly 설정
    const config = {
        responsive: true,
        displayModeBar: false  // 툴바 숨기기
    };
    
    // 🚀 Plotly 차트 생성 (매우 간단!)
    Plotly.newPlot(chartDiv, plotData, layout, config);
    
    console.log(`📈 ${selectedVariable} 트렌드 차트 렌더링 완료 (Plotly)`);
}

/**
 * CV 차트 렌더링 - Plotly 버전
 */
function renderCvChart() {
    if (!currentChartData || !currentChartData.cv_data.length) {
        console.warn('⚠️ CV 차트 데이터가 없습니다.');
        return;
    }
    
    const chartDiv = document.getElementById('cvChart');
    if (!chartDiv) {
        console.error('CV 차트 영역을 찾을 수 없습니다.');
        return;
    }
    
    const cvData = currentChartData.cv_data;
    
    // 📊 CV 값에 따른 색상 결정
    const colors = cvData.map(d => {
        if (d.cv < 5) return '#28a745';      // 낮음 (안정) - 초록
        if (d.cv < 15) return '#ffc107';     // 보통 - 노랑
        return '#dc3545';                    // 높음 (불안정) - 빨강
    });
    
    // 📊 Plotly 데이터 준비
    const plotData = [{
        x: cvData.map(d => d.variable),
        y: cvData.map(d => d.cv),
        type: 'bar',
        name: '변동계수 (%)',
        marker: {
            color: colors,
            line: {
                color: colors.map(c => c === '#28a745' ? '#1e7e34' : c === '#ffc107' ? '#e0a800' : '#c82333'),
                width: 1
            }
        },
        text: cvData.map(d => `${d.cv.toFixed(1)}%`),
        textposition: 'outside'
    }];
    
    // 📊 Plotly 레이아웃 설정
    const layout = {
        title: {
            text: '공정 안정성 평가 (변동계수)',
            font: { size: 14, color: '#333' }
        },
        xaxis: {
            title: '변수명',
            tickangle: -90,  // X축 틱을 90도로 회전
            automargin: true,  // 자동 마진 조정
            showgrid: false
        },
        yaxis: {
            title: '변동계수 (%)',
            automargin: true,  // 자동 마진 조정
            showgrid: true,
            gridcolor: '#e6e6e6',
            zeroline: true
        },
        autosize: true,  // 컨테이너 크기에 자동 맞춤
        showlegend: false,
        plot_bgcolor: '#fafafa',
        paper_bgcolor: '#ffffff'
    };
    
    // 📊 Plotly 설정
    const config = {
        responsive: true,
        displayModeBar: false  // 툴바 숨기기
    };
    
    // 🚀 Plotly 차트 생성 (매우 간단!)
    Plotly.newPlot(chartDiv, plotData, layout, config);
    
    console.log('📊 CV 차트 렌더링 완료 (Plotly)');
}

/**
 * 변수 드롭다운 업데이트
 */
function updateVariableDropdown() {
    const dropdown = document.getElementById('variableSelect');
    if (!dropdown) {
        console.error('변수 선택 드롭다운을 찾을 수 없습니다.');
        return;
    }
    
    dropdown.innerHTML = '';
    
    if (currentChartData && currentChartData.variables) {
        currentChartData.variables.forEach((variable, index) => {
            const option = document.createElement('option');
            option.value = variable;
            option.textContent = variable;
            dropdown.appendChild(option);
            
            // 첫 번째 변수를 기본 선택
            if (index === 0) {
                option.selected = true;
            }
        });
        
        // 드롭다운 변경 이벤트
        dropdown.onchange = function() {
            const selectedVariable = this.value;
            if (selectedVariable) {
                updateTrendChart(selectedVariable);
            }
        };
    }
}

/**
 * 차트 로딩 상태 표시/숨기기
 */
function showChartLoading(show) {
    // 차트 생성 버튼 상태 변경
    const chartBtn = document.getElementById('chartGenerateBtn');
    if (chartBtn) {
        chartBtn.disabled = show;
        chartBtn.innerHTML = show 
            ? '<i class="fas fa-spinner fa-spin me-2"></i>분석 중...<small class="ms-2" style="font-size: 10px; opacity: 0.8;">잠시만 기다려주세요</small>'
            : '<i class="fas fa-chart-line me-2"></i>차트 분석<small class="ms-2" style="font-size: 10px; opacity: 0.8;"><i class="fas fa-bolt"></i> 빠른처리</small>';
    }
}

/**
 * 차트 컨테이너 표시/숨기기 - Plotly 버전 (매우 간단!)
 */
function showChartContainer(show) {
    // 전체 차트 영역 표시
    const chartSection = document.getElementById('chartAnalysisContainer');
    if (chartSection) {
        chartSection.style.display = show ? 'block' : 'none';
    }
    
    // Plotly는 자동으로 반응형이므로 복잡한 설정 불필요! 🚀
    console.log(`📊 차트 컨테이너 ${show ? '표시' : '숨김'} (Plotly 자동 반응형)`);
}

console.log('PIMS 배치요약 통계 모듈이 로드되었습니다.'); 