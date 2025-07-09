/**
 * PIMS 공정정보 조회 시스템 JavaScript
 * 초보자용 - 바닐라 JavaScript로 작성 (DataTables만 jQuery 사용)
 */

// ========================================
// 1. 전역 변수 및 기본 설정
// ========================================

// DataTables 객체를 저장할 변수 (jQuery 필요)
let pimsDataTable = null;

// API 기본 URL
const API_BASE_URL = '/api/pims';

// ========================================
// 2. 페이지 로드 완료 후 실행되는 메인 함수
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('PIMS 페이지가 로드되었습니다.');
    
    // 이벤트 리스너 등록
    setupEventListeners();
    
    // 초기 상태 설정
    resetForm();
});

// ========================================
// 3. 이벤트 리스너 설정 함수
// ========================================
function setupEventListeners() {
    console.log('이벤트 리스너를 설정합니다.');
    
    // 제품 타입 선택 시
    const productTypeSelect = document.getElementById('productType1');
    productTypeSelect.addEventListener('change', function() {
        const selectedType = this.value;
        console.log('선택된 제품 타입:', selectedType);
        
        // 타입이 변경되면 하위 요소들 초기화
        resetBatchAndProcess();
        document.getElementById('itemCode1').value = ''; // 품목코드도 초기화
    });
    
    // 품목코드 입력 시 (타이핑 멈춘 후 500ms 후 실행)
    let itemCodeTimer = null;
    const itemCodeInput = document.getElementById('itemCode1');
    
    itemCodeInput.addEventListener('input', function() {
        clearTimeout(itemCodeTimer);
        const itemCode = this.value.trim();
        
        if (itemCode.length >= 3) { // 3글자 이상 입력했을 때만
            itemCodeTimer = setTimeout(function() {
                // 제품 타입이 선택되었는지 확인
                const productType = document.getElementById('productType1').value;
                if (!productType) {
                    showAlert('제품 타입을 먼저 선택해주세요.', 'warning');
                    resetBatchAndProcess();
                    return;
                }
                
                console.log('품목코드 검색:', itemCode, '제품 타입:', productType);
                searchBatches(itemCode);
            }, 500);
        } else {
            // 3글자 미만이면 배치/공정 초기화
            resetBatchAndProcess();
        }
    });
    
    // 배치 선택 시
    const batchSelect = document.getElementById('batchSelect1');
    batchSelect.addEventListener('change', function() {
        const selectedBatch = this.value;
        console.log('선택된 배치:', selectedBatch);
        
        if (selectedBatch) {
            const itemCode = itemCodeInput.value.trim();
            searchProcesses(itemCode, selectedBatch);
        } else {
            resetProcess();
        }
    });
    
    // 조회 폼 제출 시 (조회 버튼 클릭)
    const pimsDataForm = document.getElementById('pimsDataForm');
    pimsDataForm.addEventListener('submit', function(e) {
        e.preventDefault(); // 기본 폼 제출 방지
        console.log('데이터 조회 버튼이 클릭되었습니다.');
        
        searchPimsData();
    });
}

// ========================================
// 4. API 호출 함수들
// ========================================

/**
 * 품목코드로 배치 목록 조회
 * @param {string} itemCode - 품목코드 (예: 029124A)
 */
function searchBatches(itemCode) {
    console.log('배치 목록을 조회합니다:', itemCode);
    
    // 로딩 상태 표시
    showLoadingForSelect('batchSelect1', '배치 조회 중...');
    
    // API 호출 (fetch 사용)
    fetch(`${API_BASE_URL}/search-product`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            itemcode: itemCode,
            batch_no: "",     // 모든 배치 조회
            proc_code: ""
        })
    })
    .then(response => response.json()) // JSON 응답 파싱
    .then(data => {
        console.log('배치 조회 성공:', data);
        
        if (data.success && data.data) {
            updateBatchOptions(data.data);
        } else {
            showAlert('배치 조회에 실패했습니다.', 'warning');
            resetBatchAndProcess();
        }
    })
    .catch(error => {
        console.error('배치 조회 오류:', error);
        showAlert('배치 조회 중 오류가 발생했습니다.', 'danger');
        resetBatchAndProcess();
    });
}

/**
 * 선택된 배치의 공정 목록 조회
 * @param {string} itemCode - 품목코드
 * @param {string} batchNo - 배치번호
 */
function searchProcesses(itemCode, batchNo) {
    console.log('공정 목록을 조회합니다:', itemCode, batchNo);
    
    // 로딩 상태 표시
    showLoadingForSelect('processSelect1', '공정 조회 중...');
    
    // API 호출 (fetch 사용)
    fetch(`${API_BASE_URL}/search-product`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            itemcode: itemCode,
            batch_no: batchNo,
            proc_code: ""     // 모든 공정 조회
        })
    })
    .then(response => response.json()) // JSON 응답 파싱
    .then(data => {
        console.log('공정 조회 성공:', data);
        
        if (data.success && data.data) {
            updateProcessOptions(data.data);
        } else {
            showAlert('공정 조회에 실패했습니다.', 'warning');
            resetProcess();
        }
    })
    .catch(error => {
        console.error('공정 조회 오류:', error);
        showAlert('공정 조회 중 오류가 발생했습니다.', 'danger');
        resetProcess();
    });
}

/**
 * PIMS 데이터 조회 (메인 기능)
 * 사용자가 선택한 제품 타입에 따라 해당 API 직접 호출
 */
function searchPimsData() {
    console.log('PIMS 데이터를 조회합니다.');
    
    // 제품 타입 수집
    const productType = document.getElementById('productType1').value;
    
    // 폼 데이터 수집
    const formData = {
        itemcode: document.getElementById('itemCode1').value.trim(),
        batch_no: document.getElementById('batchSelect1').value,
        proc_code: document.getElementById('processSelect1').value,
        start_time: document.getElementById('startTime1').value,
        end_time: document.getElementById('endTime1').value,
        limit: 50   // 화면 표시용 (다운로드는 별도 구현 예정)
    };
    
    // 필수 입력 검증
    if (!productType) {
        showAlert('제품 타입을 먼저 선택해주세요.', 'warning');
        return;
    }
    
    if (!formData.itemcode || !formData.batch_no || !formData.proc_code) {
        showAlert('품목코드, 배치, 공정을 모두 선택해주세요.', 'warning');
        return;
    }
    
    console.log('조회할 데이터:', formData, '제품 타입:', productType);
    
    // 조회 버튼 비활성화
    const searchBtn = document.getElementById('searchBtn1');
    searchBtn.disabled = true;
    
    // 선택한 제품 타입에 따라 API 호출
    let apiPromise;
    let typeName;
    
    if (productType === 'basic') {
        // 기존고형제 조회
        typeName = '기존고형제';
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>기존고형제 조회 중...';
        apiPromise = searchBasicData(formData);
    } else if (productType === 'l23') {
        // 스마트고형제 조회  
        typeName = '스마트고형제';
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>스마트고형제 조회 중...';
        apiPromise = searchL23Data(formData);
    } else {
        showAlert('올바른 제품 타입을 선택해주세요.', 'warning');
        searchBtn.disabled = false;
        return;
    }
    
    // API 호출 실행
    apiPromise
        .then(data => {
            if (data && data.length > 0) {
                // 데이터 조회 성공
                console.log(`${typeName}에서 ${data.length}건 조회됨`);
                displayPimsData(data);
                showAlert(`${typeName} 데이터 조회 완료! ${data.length}건의 데이터를 찾았습니다.`, 'success');
            } else {
                // 0건 조회
                showAlert(`${typeName}에서 조회된 데이터가 없습니다.`, 'info');
            }
        })
        .catch(error => {
            console.error('PIMS 데이터 조회 오류:', error);
            showAlert(`${typeName} 데이터 조회 중 오류가 발생했습니다.`, 'danger');
        })
        .finally(() => {
            // 조회 버튼 다시 활성화
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>데이터 조회';
        });
}

/**
 * 기존고형제 데이터 조회
 * @param {Object} formData - 조회 파라미터
 * @returns {Promise} - 조회 결과 데이터
 */
function searchBasicData(formData) {
    console.log('기존고형제 API 호출');
    
    return fetch(`${API_BASE_URL}/get-data-basic`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('기존고형제 조회 응답:', data);
        
        if (data.success && data.data) {
            return data.data;
        } else {
            return []; // 0건
        }
    });
}

/**
 * 스마트고형제 데이터 조회
 * @param {Object} formData - 조회 파라미터
 * @returns {Promise} - 조회 결과 데이터
 */
function searchL23Data(formData) {
    console.log('스마트고형제 API 호출');
    
    return fetch(`${API_BASE_URL}/get-data-l23`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('스마트고형제 조회 응답:', data);
        
        if (data.success && data.data) {
            return data.data;
        } else {
            return []; // 0건
        }
    });
}

// ========================================
// 5. UI 업데이트 함수들
// ========================================

/**
 * 배치 선택 옵션 업데이트
 * @param {Array} batches - 배치 목록 데이터
 */
function updateBatchOptions(batches) {
    const batchSelect = document.getElementById('batchSelect1');
    
    // 기존 옵션 제거
    batchSelect.innerHTML = '';
    
    // 기본 옵션 추가
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '배치를 선택하세요';
    batchSelect.appendChild(defaultOption);
    
    // 중복 제거를 위한 Set 사용 (CHARG = 배치번호)
    const uniqueBatches = [...new Set(batches.map(item => item.CHARG))];
    
    // 새 옵션 추가
    uniqueBatches.forEach(function(batchNo) {
        if (batchNo) { // 빈 값이 아닌 경우만
            const option = document.createElement('option');
            option.value = batchNo;
            option.textContent = batchNo;
            batchSelect.appendChild(option);
        }
    });
    
    // 배치 선택 활성화
    batchSelect.disabled = false;
    
    console.log(`배치 목록 업데이트 완료: ${uniqueBatches.length}개`);
}

/**
 * 공정 선택 옵션 업데이트
 * @param {Array} processes - 공정 목록 데이터
 */
function updateProcessOptions(processes) {
    const processSelect = document.getElementById('processSelect1');
    
    // 디버깅: 공정 데이터 확인
    console.log('받은 공정 데이터:', processes);
    
    // 기존 옵션 제거
    processSelect.innerHTML = '';
    
    // 기본 옵션 추가
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '공정을 선택하세요';
    processSelect.appendChild(defaultOption);
    
    // 중복 제거를 위한 Set 사용 (KTSCH = 공정코드)
    const uniqueProcesses = [...new Set(processes.map(item => item.KTSCH))];
    
    // 새 옵션 추가
    uniqueProcesses.forEach(function(procCode) {
        if (procCode) { // 빈 값이 아닌 경우만
            const option = document.createElement('option');
            option.value = procCode;
            option.textContent = procCode;
            processSelect.appendChild(option);
        }
    });
    
    // 공정 선택 활성화
    processSelect.disabled = false;
    
    console.log(`공정 목록 업데이트 완료: ${uniqueProcesses.length}개`);
}

/**
 * PIMS 데이터를 DataTables로 표시 (여기만 jQuery 사용)
 * @param {Array} data - PIMS 데이터 배열
 */
function displayPimsData(data) {
    console.log('DataTables로 데이터를 표시합니다:', data.length, '건');
    
    // 결과 영역 표시
    const resultContainer = document.getElementById('resultContainer1');
    resultContainer.classList.remove('d-none');
    
    // 기존 테이블이 있다면 제거 (jQuery 사용)
    if (pimsDataTable) {
        pimsDataTable.destroy();
        const existingTable = document.getElementById('pimsTable1');
        if (existingTable) {
            existingTable.remove();
        }
    }
    
    // 테이블 HTML 생성
    const tableHtml = `
        <div class="card shadow-ckd">
            <div class="card-header result-header d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-0">
                        <i class="fas fa-table me-2"></i>
                        조회 결과 (${data.length}건만 표시)
                        <small class="text-muted ms-3">
                            <i class="fas fa-info-circle me-1"></i>
                            소수점 4째자리에서 반올림 적용
                        </small>
                    </h6>
                </div>
                <div>
                    <button type="button" 
                            class="btn btn-outline-success btn-sm" 
                            id="downloadCsvBtn"
                            title="모든 데이터를 CSV 파일로 다운로드">
                        <i class="fas fa-download me-2"></i>
                        CSV 다운로드
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table id="pimsTable1" class="table table-striped table-hover">
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
    
    // 결과 컨테이너에 테이블 추가
    resultContainer.innerHTML = tableHtml;
    
    // 첫 번째 데이터로 컬럼 정보 생성
    if (data.length > 0) {
        const columns = Object.keys(data[0]).map(key => ({
            title: key,
            data: key,
            render: function(data, type, row) {
                if (data === null || data === undefined) {
                    return '';
                }
                
                // 숫자 데이터인지 확인 (소수점이 있는 경우)
                if (typeof data === 'number' && data % 1 !== 0) {
                    // 소수점 4째자리에서 반올림 → 4째자리까지 표시
                    return parseFloat(data.toFixed(4));
                }
                
                // 시간 데이터 포맷 변경 (T 제거)
                if (typeof data === 'string' && data.includes('T')) {
                    // 2024-07-24T07:01:12 → 2024-07-24 07:01:12
                    return data.replace('T', ' ').split('.')[0]; // .000 제거
                }
                
                return data;
            }
        }));
        
        // DataTables 초기화 (여기만 jQuery 사용!)
        pimsDataTable = $('#pimsTable1').DataTable({
            data: data,
            columns: columns,
            responsive: false,          // 반응형 테이블 비활성화 (한 줄 표시를 위해)
            scrollX: true,             // 가로 스크롤 활성화
            autoWidth: false,          // 자동 폭 조정 비활성화
            columnDefs: [              // 모든 컬럼에 대한 설정
                {
                    targets: '_all',   // 모든 컬럼에 적용
                    className: 'dt-nowrap', // 줄바꿈 방지 클래스
                    render: function(data, type, row) {
                        if (type === 'display' && data != null) {
                            return '<span style="white-space: nowrap;">' + data + '</span>';
                        }
                        return data;
                    }
                }
            ],
            pageLength: 7,             // 페이지당 7건 표시
            lengthMenu: [7, 15, 25, 50],  // 페이지당 표시 건수 옵션
            language: {
                // 한국어 설정
                search: "검색:",
                lengthMenu: "페이지당 _MENU_ 건 표시",
                info: "총 _TOTAL_건 중 _START_-_END_건 표시",
                infoEmpty: "데이터가 없습니다",
                infoFiltered: "(전체 _MAX_건에서 필터링)",
                paginate: {
                    first: "처음",
                    last: "마지막", 
                    next: "다음",
                    previous: "이전"
                }
            },
            order: [[0, 'desc']],      // 첫 번째 컬럼 기준 내림차순 정렬
            createdRow: function(row, data, index) {
                // 생성된 행의 모든 셀에 강제로 nowrap 적용
                $(row).find('td').css({
                    'white-space': 'nowrap',
                    'word-wrap': 'normal',
                    'word-break': 'keep-all',
                    'text-overflow': 'clip',
                    'overflow': 'visible'
                });
            }
        });
        
        console.log('DataTables 초기화 완료');
        
        // CSV 다운로드 버튼 이벤트 리스너 추가
        const downloadBtn = document.getElementById('downloadCsvBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function() {
                console.log('CSV 다운로드 버튼 클릭됨');
                downloadAllDataAsCSV();
            });
        }
    }
}

// ========================================
// 새로운 함수: CSV 다운로드 기능
// ========================================

/**
 * 모든 PIMS 데이터를 CSV 파일로 다운로드
 * limit=0으로 설정해서 모든 데이터를 가져온 후 CSV로 변환
 */
function downloadAllDataAsCSV() {
    console.log('CSV 다운로드를 시작합니다...');
    
    // 다운로드 버튼 비활성화 및 로딩 표시
    const downloadBtn = document.getElementById('downloadCsvBtn');
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>다운로드 중...';
    
    // 제품 타입 확인
    const productType = document.getElementById('productType1').value;
    
    // 폼 데이터 수집 (limit=0으로 설정해서 모든 데이터 조회)
    const formData = {
        itemcode: document.getElementById('itemCode1').value.trim(),
        batch_no: document.getElementById('batchSelect1').value,
        proc_code: document.getElementById('processSelect1').value,
        start_time: document.getElementById('startTime1').value,
        end_time: document.getElementById('endTime1').value,
        limit: 0   // 모든 데이터 조회
    };
    
    console.log('다운로드용 데이터 조회:', formData, '제품 타입:', productType);
    
    // 선택한 제품 타입에 따라 API 호출
    let apiPromise;
    if (productType === 'basic') {
        apiPromise = searchBasicData(formData);
    } else if (productType === 'l23') {
        apiPromise = searchL23Data(formData);
    } else {
        showAlert('제품 타입을 먼저 선택해주세요.', 'warning');
        resetDownloadButton();
        return;
    }
    
    // API 호출 및 CSV 생성
    apiPromise
        .then(data => {
            if (data && data.length > 0) {
                console.log(`다운로드용 데이터 조회 완료: ${data.length}건`);
                
                // CSV 파일 생성 및 다운로드
                generateAndDownloadCSV(data, formData);
                
                showAlert(`CSV 다운로드 완료! ${data.length}건의 데이터를 다운로드했습니다.`, 'success');
            } else {
                showAlert('다운로드할 데이터가 없습니다.', 'info');
            }
        })
        .catch(error => {
            console.error('CSV 다운로드 오류:', error);
            showAlert('CSV 다운로드 중 오류가 발생했습니다.', 'danger');
        })
        .finally(() => {
            // 다운로드 버튼 복원
            resetDownloadButton();
        });
}

/**
 * CSV 파일 생성 및 다운로드 실행
 * @param {Array} data - 다운로드할 데이터 배열 
 * @param {Object} formData - 폼 데이터 (파일명 생성용)
 */
function generateAndDownloadCSV(data, formData) {
    console.log('CSV 파일을 생성합니다...');
    
    if (!data || data.length === 0) {
        console.log('CSV 생성할 데이터가 없습니다.');
        return;
    }
    
    // CSV 헤더 생성 (첫 번째 데이터의 키들)
    const headers = Object.keys(data[0]);
    let csvContent = headers.join(',') + '\n';
    
    // CSV 데이터 생성 (소수점 4째자리 반올림 적용)
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
    
    // 파일명 생성 (현재 날짜 포함)
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
    const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, ''); // HHMMSS
    const fileName = `PIMS_데이터_${formData.itemcode}_${formData.batch_no}_${formData.proc_code}_${dateStr}_${timeStr}.csv`;
    
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
        
        console.log(`CSV 파일 다운로드 완료: ${fileName}`);
    } else {
        console.error('브라우저에서 파일 다운로드를 지원하지 않습니다.');
        showAlert('브라우저에서 파일 다운로드를 지원하지 않습니다.', 'danger');
    }
}

/**
 * 다운로드 버튼을 원래 상태로 복원
 */
function resetDownloadButton() {
    const downloadBtn = document.getElementById('downloadCsvBtn');
    if (downloadBtn) {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>CSV 다운로드';
    }
}

// ========================================
// 6. 유틸리티 함수들
// ========================================

/**
 * 폼 초기화
 */
function resetForm() {
    document.getElementById('itemCode1').value = '';
    resetBatchAndProcess();
}

/**
 * 배치 및 공정 선택 초기화
 */
function resetBatchAndProcess() {
    resetBatch();
    resetProcess();
}

/**
 * 배치 선택 초기화
 */
function resetBatch() {
    const batchSelect = document.getElementById('batchSelect1');
    batchSelect.innerHTML = '<option value="">품목코드 입력 후 선택</option>';
    batchSelect.disabled = true;
}

/**
 * 공정 선택 초기화
 */
function resetProcess() {
    const processSelect = document.getElementById('processSelect1');
    processSelect.innerHTML = '<option value="">배치 선택 후 선택</option>';
    processSelect.disabled = true;
}

/**
 * 셀렉트 박스에 로딩 상태 표시
 * @param {string} elementId - 셀렉트 박스 ID
 * @param {string} message - 로딩 메시지
 */
function showLoadingForSelect(elementId, message) {
    const selectElement = document.getElementById(elementId);
    selectElement.innerHTML = `<option value="">${message}</option>`;
    selectElement.disabled = true;
}

/**
 * 알림 메시지 표시
 * @param {string} message - 메시지 내용
 * @param {string} type - 알림 타입 (success, warning, danger, info)
 */
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-info-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.getElementById('alert-container');
    alertContainer.innerHTML = alertHtml;
    
    // 3초 후 자동 제거
    setTimeout(function() {
        const alertElement = alertContainer.querySelector('.alert');
        if (alertElement) {
            alertElement.style.opacity = '0';
            setTimeout(() => alertElement.remove(), 300);
        }
    }, 3000);
    
    console.log(`알림 표시: [${type}] ${message}`);
}
