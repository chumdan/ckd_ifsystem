/**
 * LIMS 실험결과 기능 JavaScript
 * PIMS 배치요약과 유사하지만 시간 정보와 제품 타입 구분 없이 단순화
 */

// ========================================
// 1. LIMS API URL 및 변수
// ========================================

// LIMS API 기본 URL
const LIMS_API_BASE_URL = '/api/lims';

// LIMS DataTables 객체
let limsStatsTable = null;

// Plotly 차트 변수들
let currentLimsChartData = null;  // 현재 차트 데이터 저장

// ========================================
// 2. 페이지 로드 완료 후 LIMS 기능 초기화
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('LIMS 실험결과 기능이 로드되었습니다.');
    
    // 폼 제출 이벤트 리스너 등록
    initializeLimsEventListeners();
});

// ========================================
// 3. 이벤트 리스너 초기화
// ========================================
function initializeLimsEventListeners() {
    // 품목코드 입력 이벤트
    const itemCodeInput = document.getElementById('itemCode1');
    if (itemCodeInput) {
        itemCodeInput.addEventListener('input', debounce(handleItemCodeInput, 500));
    }
    
    // 배치 선택 이벤트
    const batchSelect = document.getElementById('batchSelect1');
    if (batchSelect) {
        batchSelect.addEventListener('change', handleBatchSelection);
    }
    
    // 폼 제출 이벤트
    const limsForm = document.getElementById('limsDataForm');
    if (limsForm) {
        limsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            searchLimsData();
        });
    }
    
    // 실험항목 선택 드롭다운 (PIMS와 동일하게 자동 차트 업데이트)
    const variableSelect = document.getElementById('chartVariableSelect1');
    if (variableSelect) {
        variableSelect.addEventListener('change', generateChartsFromCachedData);
    }
    
    // CV 다운로드 버튼
    const downloadCvBtn = document.getElementById('downloadCvBtn1');
    if (downloadCvBtn) {
        downloadCvBtn.addEventListener('click', downloadCvResults);
    }
    
    console.log('✅ LIMS 이벤트 리스너가 등록되었습니다.');
}

// ========================================
// 4. 품목코드 입력 처리
// ========================================
function handleItemCodeInput() {
    const itemCode = document.getElementById('itemCode1').value.trim();
    
    if (itemCode.length >= 3) {
        console.log('품목코드 입력됨:', itemCode);
        searchLimsProduct(itemCode);
    } else {
        // 입력이 짧으면 배치/공정 선택 초기화
        resetBatchAndProcessSelects();
    }
}

function searchLimsProduct(itemCode) {
    console.log('🔍 LIMS 품목 조회 시작:', itemCode);
    
    showLimsLoading(true);
    
    fetch(`${LIMS_API_BASE_URL}/search-product`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            itemcode: itemCode,
            batch_no: "",
            proc_code: ""
        })
    })
    .then(response => response.json())
    .then(data => {
        showLimsLoading(false);
        
        if (data.success) {
            console.log('✅ LIMS 품목 조회 성공:', data.data);
            updateBatchOptions(data.data.batches);
            updateProcessOptions(data.data.processes);
        } else {
            console.error('❌ LIMS 품목 조회 실패:', data.detail);
            showErrorAlert('품목 조회 실패: ' + data.detail);
            resetBatchAndProcessSelects();
        }
    })
    .catch(error => {
        showLimsLoading(false);
        console.error('❌ LIMS 품목 조회 오류:', error);
        showErrorAlert('품목 조회 중 오류가 발생했습니다.');
        resetBatchAndProcessSelects();
    });
}

// ========================================
// 5. 배치/공정 선택 업데이트
// ========================================
function updateBatchOptions(batches) {
    const batchSelect = document.getElementById('batchSelect1');
    if (!batchSelect) return;
    
    // 기존 옵션 제거
    batchSelect.innerHTML = '';
    
    if (batches && batches.length > 0) {
        batches.forEach(batch => {
            const option = document.createElement('option');
            option.value = batch.KBATCH;
            option.textContent = batch.batch_display || batch.KBATCH;
            batchSelect.appendChild(option);
        });
        
        batchSelect.disabled = false;
        console.log(`✅ 배치 옵션 업데이트 완료: ${batches.length}개`);
    } else {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '조회된 배치가 없습니다';
        batchSelect.appendChild(option);
        batchSelect.disabled = true;
    }
}

function updateProcessOptions(processes) {
    const processSelect = document.getElementById('processSelect1');
    if (!processSelect) return;
    
    // 기존 옵션 제거
    processSelect.innerHTML = '';
    
    if (processes && processes.length > 0) {
        // 기본 선택 옵션
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '공정을 선택하세요';
        processSelect.appendChild(defaultOption);
        
        processes.forEach(process => {
            const option = document.createElement('option');
            option.value = process.KTSCH;
            option.textContent = process.process_display || `${process.KTSCH} - ${process.PROCESS_NAME_KOR}`;
            processSelect.appendChild(option);
        });
        
        processSelect.disabled = false;
        console.log(`✅ 공정 옵션 업데이트 완료: ${processes.length}개`);
    } else {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '조회된 공정이 없습니다';
        processSelect.appendChild(option);
        processSelect.disabled = true;
    }
}

function resetBatchAndProcessSelects() {
    const batchSelect = document.getElementById('batchSelect1');
    const processSelect = document.getElementById('processSelect1');
    
    if (batchSelect) {
        batchSelect.innerHTML = '<option value="">품목코드 입력 후 선택</option>';
        batchSelect.disabled = true;
    }
    
    if (processSelect) {
        processSelect.innerHTML = '<option value="">배치 선택 후 선택</option>';
        processSelect.disabled = true;
    }
}

function handleBatchSelection() {
    const processSelect = document.getElementById('processSelect1');
    if (processSelect && !processSelect.disabled) {
        console.log('배치가 선택되었습니다. 공정 선택이 활성화됩니다.');
    }
}

// ========================================
// 6. LIMS 데이터 조회 메인 함수
// ========================================
function searchLimsData() {
    console.log('LIMS 실험결과 조회를 시작합니다.');
    
    // 폼 데이터 수집
    const formData = collectLimsFormData();
    
    if (!formData) {
        console.error('❌ 폼 데이터 수집 실패');
        return;
    }
    
    console.log('📝 수집된 폼 데이터:', formData);
    
    // LIMS 데이터 조회 실행
    searchLimsDataAPI(formData);
}

function collectLimsFormData() {
    const itemCode = document.getElementById('itemCode1').value.trim();
    const batchSelect = document.getElementById('batchSelect1');
    const processSelect = document.getElementById('processSelect1');
    
    // 필수 필드 검증
    if (!itemCode) {
        showErrorAlert('품목코드를 입력해주세요.');
        return null;
    }
    
    if (!batchSelect || batchSelect.selectedOptions.length === 0) {
        showErrorAlert('배치를 선택해주세요.');
        return null;
    }
    
    if (!processSelect || !processSelect.value) {
        showErrorAlert('공정을 선택해주세요.');
        return null;
    }
    
    // 선택된 배치들 수집
    const selectedBatches = Array.from(batchSelect.selectedOptions).map(option => option.value);
    
    return {
        itemcode: itemCode,
        batch_no: selectedBatches.join(','),
        proc_code: processSelect.value
    };
}

function searchLimsDataAPI(formData) {
    console.log('🔍 LIMS API 호출 시작:', formData);
    
    showLimsLoading(true);
    hideResultContainer();
    
    fetch(`${LIMS_API_BASE_URL}/get-lims-data`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        showLimsLoading(false);
        
        if (data.success) {
            console.log('✅ LIMS 데이터 조회 성공:', data);
            handleLimsResponse(data);
        } else {
            console.error('❌ LIMS 데이터 조회 실패:', data.detail);
            showErrorAlert('LIMS 데이터 조회 실패: ' + data.detail);
        }
    })
    .catch(error => {
        showLimsLoading(false);
        console.error('❌ LIMS API 호출 오류:', error);
        showErrorAlert('LIMS 데이터 조회 중 오류가 발생했습니다.');
    });
}

// ========================================
// 7. LIMS 데이터 응답 처리
// ========================================
function handleLimsResponse(data) {
    console.log('LIMS 응답 데이터 처리 중:', data);
    
    if (data.data && data.data.length > 0) {
        displayLimsData(data.data);
        showLimsInfo(data.data.length, data.total_batches);
        
        // 차트 데이터 저장 (차트 기능용)
        currentLimsChartData = data.data;
        
        // 차트 분석 자동 표시
        showChartAnalysis(data.data);
    } else {
        showInfoAlert('조회 조건에 맞는 LIMS 데이터가 없습니다.');
    }
}

function displayLimsData(data) {
    console.log('LIMS 데이터 테이블 생성 중...', data.length + '건');
    
    if (data.length === 0) {
        showInfoAlert('조회된 LIMS 데이터가 없습니다.');
        return;
    }
    
    // 기존 테이블이 있으면 제거
    if (limsStatsTable) {
        limsStatsTable.destroy();
        limsStatsTable = null;
    }
    
    // 테이블 컨테이너 생성
    const container = document.getElementById('statsTableContainer');
    if (!container) return;
    
    // 컬럼 정의 생성
    const columns = createLimsColumns(data[0]);
    
    // HTML 테이블 생성
    const tableHTML = createLimsTableHTML(data, columns);
    
    // 테이블 HTML 삽입 (PIMS와 동일한 구조)
    container.innerHTML = `
        <div class="card shadow-ckd">
            <div class="card-header result-header d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-0">
                        <i class="fas fa-table me-2"></i>
                        LIMS 원본 실험데이터 (${data.length}건)
                    </h6>
                </div>
                <div>
                    <button type="button" 
                            class="btn btn-outline-success btn-sm" 
                            onclick="downloadAllLimsDataAsCSV()" 
                            title="전체 데이터 CSV 다운로드">
                        <i class="fas fa-download me-2"></i>
                        CSV 다운로드
                    </button>
                </div>
            </div>
            <div class="card-body">
                ${tableHTML}
            </div>
        </div>
    `;
    
    // DataTables 초기화
    const tableElement = document.getElementById('limsStatsTable');
    if (tableElement) {
        limsStatsTable = $(tableElement).DataTable({
            responsive: true,
            pageLength: 8,
            lengthMenu: [[8, 15, 25, 50, -1], [8, 15, 25, 50, "전체"]],
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
            order: [[0, 'asc']],
            scrollX: true,
            fixedColumns: {
                leftColumns: 1
            }
        });
        
        console.log('✅ LIMS DataTables 초기화 완료');
    }
    
    // 결과 컨테이너 표시
    showResultContainer();
}

function createLimsColumns(sampleRow) {
    if (!sampleRow) return [];
    
    // LIMS는 원본 실험데이터를 그대로 표시하므로 모든 컬럼을 순서대로 표시
    return Object.keys(sampleRow);
}

function createLimsTableHTML(data, columns) {
    let html = `
        <div class="table-responsive">
            <table id="limsStatsTable" class="table table-striped table-hover lims-table">
                <thead>
                    <tr>
    `;
    
    // 헤더 생성
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    
    html += `
                    </tr>
                </thead>
                <tbody>
    `;
    
    // 데이터 행 생성
    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            const value = row[col];
            const displayValue = value !== null && value !== undefined ? value : '-';
            html += `<td>${displayValue}</td>`;
        });
        html += '</tr>';
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

// ========================================
// 8. 차트 기능
// ========================================
function showChartAnalysis(limsData) {
    console.log('LIMS 차트 분석 표시 중...', limsData.length + '건');
    
    if (!limsData || limsData.length === 0) {
        console.log('차트 표시할 데이터가 없습니다.');
        return;
    }
    
    // 차트 분석 컨테이너 표시
    const chartContainer = document.getElementById('chartAnalysisContainer');
    if (chartContainer) {
        chartContainer.style.display = 'block';
        
        // 실험항목 드롭다운 업데이트
        updateVariableDropdown(limsData);
        
        // PIMS와 동일하게 자동으로 차트 생성 (버튼 없이 바로)
        autoGenerateCharts();
    }
}

// PIMS와 동일한 자동 차트 생성 로직
function autoGenerateCharts() {
    const select = document.getElementById('chartVariableSelect1');
    
    if (select && select.options.length > 1) {
        // 첫 번째 실험항목을 자동 선택 (첫 번째는 "실험항목을 선택하세요"이므로 두 번째)
        select.selectedIndex = 1;
        
        // 자동으로 차트 생성 (PIMS와 동일)
        generateChartsFromCachedData();
    }
}

function updateVariableDropdown(data) {
    const select = document.getElementById('chartVariableSelect1');
    if (!select || !data || data.length === 0) return;
    
    // 기존 옵션 제거
    select.innerHTML = '<option value="">실험항목을 선택하세요</option>';
    
    // 숫자형 FINAL 값을 가진 ANALYTE들 추출
    const analyteSet = new Set();
    
    data.forEach(row => {
        const analyte = row.ANALYTE;
        const finalValue = row.FINAL;
        
        // ANALYTE와 FINAL이 존재하고, FINAL이 순수 숫자인 경우만
        if (analyte && finalValue && isNumericValue(finalValue)) {
            analyteSet.add(analyte);
        }
    });
    
    // ANALYTE들을 정렬하여 옵션 추가
    Array.from(analyteSet).sort().forEach(analyte => {
        const option = document.createElement('option');
        option.value = analyte;
        option.textContent = analyte;
        select.appendChild(option);
    });
    
    console.log(`✅ LIMS 실험항목 드롭다운 업데이트 완료: ${analyteSet.size}개 항목`);
}

// 숫자 값 판별 함수 (LIMS 전용)
function isNumericValue(value) {
    if (!value || typeof value !== 'string') return false;
    
    // 문자열 값 제외 (PASS, Pass, 적합 등)
    if (/^[a-zA-Z가-힣]+$/.test(value.trim())) return false;
    
    // 범위 값 제외 (100.0-102.2, 99-101 등)
    if (value.includes('-') && value.split('-').length === 2) return false;
    
    // 순수 숫자인지 확인
    const num = parseFloat(value.trim());
    return !isNaN(num) && isFinite(num);
}

function generateChartsFromCachedData() {
    if (!currentLimsChartData) {
        console.log('차트 생성할 데이터가 없습니다.');
        return;
    }
    
    const selectedAnalyte = document.getElementById('chartVariableSelect1').value;
    
    if (!selectedAnalyte) {
        console.log('실험항목이 선택되지 않았습니다.');
        return;
    }
    
    console.log('선택된 실험항목으로 차트 생성:', selectedAnalyte);
    
    // 트렌드 차트 업데이트
    updateTrendChart(selectedAnalyte);
    
    // CV 차트 렌더링
    renderCvChart(selectedAnalyte);
}

function updateTrendChart(selectedAnalyte) {
    if (!currentLimsChartData || currentLimsChartData.length === 0) {
        console.log('트렌드 차트: 데이터가 없습니다.');
        return;
    }
    
    console.log('LIMS 트렌드 차트 업데이트:', selectedAnalyte);
    
    // 선택된 ANALYTE에 해당하고 FINAL이 숫자인 데이터만 필터링
    const filteredData = currentLimsChartData.filter(row => 
        row.ANALYTE === selectedAnalyte && isNumericValue(row.FINAL)
    );
    
    if (filteredData.length === 0) {
        console.log('선택된 실험항목에 대한 숫자 데이터가 없습니다.');
        return;
    }
    
    // 배치별로 데이터 그룹화 (LIMS 원본 데이터는 CHARG 사용)
    const batchGroups = {};
    filteredData.forEach(row => {
        const batch = row.CHARG || row.batchNo || 'Unknown';  // CHARG를 우선 사용
        const finalValue = parseFloat(row.FINAL);
        
        if (!batchGroups[batch]) {
            batchGroups[batch] = [];
        }
        batchGroups[batch].push(finalValue);
    });
    
    // 배치별 평균값으로 트렌드 차트 생성
    const batches = Object.keys(batchGroups).sort();
    const avgValues = batches.map(batch => {
        const values = batchGroups[batch];
        return values.reduce((sum, val) => sum + val, 0) / values.length;
    });
    
    // PIMS 스타일 트렌드 차트 (면적 채우기)
    const traces = [{
        x: batches,
        y: avgValues,
        type: 'scatter',
        mode: 'lines+markers',
        name: `${selectedAnalyte} 배치별 평균`,
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
        fill: 'tonexty',  // 면적 채우기
        fillcolor: 'rgba(0, 123, 255, 0.1)'  // 투명한 파란색
    }];
    
    // Y축 범위 계산 (그래프가 잘리지 않도록 충분한 여유 공간 확보)
    const minValue = Math.min(...avgValues);
    const maxValue = Math.max(...avgValues);
    const dataRange = maxValue - minValue;
    const padding = dataRange > 0 ? dataRange * 0.1 : 1; // 10% 패딩, 범위가 없으면 기본값
    
    const layout = {
        title: {
            text: `${selectedAnalyte} 배치별 트렌드`,
            font: { size: 14, color: '#333' }
        },
        xaxis: {
            title: {
                text: '배치번호',
                standoff: 30,  // CV 차트와 동일하게 설정
                font: { size: 12 }  // CV 차트와 동일하게 설정
            },
            tickangle: -90,
            tickfont: { size: 12 },
            tickpad: 15,  // CV 차트와 동일하게 설정 (적당한 간격)
            automargin: true,
            showgrid: true,
            gridcolor: '#e6e6e6'
        },
        yaxis: {
            title: '실험값',
            automargin: true,
            showgrid: true,
            gridcolor: '#e6e6e6',
            // Y축 범위를 여유롭게 설정 (그래프가 잘리지 않도록)
            range: [minValue - padding, maxValue + padding]
        },
        height: 430,
        showlegend: false,
        plot_bgcolor: '#fafafa',
        paper_bgcolor: '#ffffff',

    };
    
    const config = {
        responsive: true,
        displayModeBar: false  // PIMS와 동일하게 툴바 숨기기
    };
    
    Plotly.newPlot('trendChart1', traces, layout, config);
}

function renderCvChart(selectedAnalyte) {
    if (!currentLimsChartData || currentLimsChartData.length === 0) {
        console.log('CV 차트: 데이터가 없습니다.');
        return;
    }
    
    console.log('LIMS CV 차트 렌더링 - 실험항목별 CV 계산');
    
    // 전체 데이터에서 숫자형 FINAL 값을 가진 모든 실험항목별로 그룹화
    const analyteGroups = {};
    currentLimsChartData.forEach(row => {
        const analyte = row.ANALYTE;
        const finalValue = row.FINAL;
        
        if (analyte && finalValue && isNumericValue(finalValue)) {
            if (!analyteGroups[analyte]) {
                analyteGroups[analyte] = [];
            }
            analyteGroups[analyte].push(parseFloat(finalValue));
        }
    });
    
    console.log(`🔍 실험항목별 CV 계산:`, analyteGroups);
    
    // 실험항목별 CV 계산
    const cvData = [];
    const labels = [];
    const colors = [];
    
    Object.keys(analyteGroups).sort().forEach(analyte => {
        const values = analyteGroups[analyte];
        
        if (values.length >= 2) { // CV 계산을 위해 최소 2개 값 필요
            const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
            const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (values.length - 1);
            const std = Math.sqrt(variance);
            
            if (mean !== 0) {
                const cv = (std / Math.abs(mean)) * 100;
                
                cvData.push(cv);
                labels.push(analyte);
                
                // CV 값에 따른 색상 결정
                if (cv < 5) {
                    colors.push('#28a745'); // 녹색 (안정)
                } else if (cv < 15) {
                    colors.push('#ffc107'); // 노란색 (보통)
                } else {
                    colors.push('#dc3545'); // 빨간색 (위험)
                }
            }
        } else {
            // 값이 1개만 있는 경우 CV = 0
            cvData.push(0);
            labels.push(analyte);
            colors.push('#6c757d'); // 회색 (데이터 부족)
        }
    });
    
    // PIMS 스타일 CV 차트
    const trace = {
        x: labels,
        y: cvData,
        type: 'bar',
        name: '변동계수 (%)',
        marker: {
            color: colors,
            line: {
                color: colors.map(c => c === '#28a745' ? '#1e7e34' : c === '#ffc107' ? '#e0a800' : '#c82333'),
                width: 1
            }
        },
        text: cvData.map(cv => cv.toFixed(1) + '%'),
        textposition: 'outside'
    };
    
    // Y축 범위 동적 계산 (높은 CV 값이 잘리지 않도록)
    const maxCv = Math.max(...cvData);
    const yAxisMax = maxCv > 0 ? Math.ceil(maxCv * 1.15) : 20; // 최대값의 115%로 여유 공간 확보
    
    const layout = {
        title: {
            text: '공정 안정성 평가 - 실험항목별 변동계수(CV)',
            font: { size: 14, color: '#333' }
        },
        xaxis: {
            title: {
                text: '실험항목',
                standoff: 30,
                font: { size: 12 }
            },
            tickangle: -90,
            tickpad: 15,
            automargin: true,
            showgrid: false
        },
        yaxis: {
            title: '변동계수 (%)',
            automargin: true,
            showgrid: true,
            gridcolor: '#e6e6e6',
            zeroline: true,
            range: [0, yAxisMax] // 동적으로 Y축 범위 설정
        },
        height: 430,
        showlegend: false,
        plot_bgcolor: '#fafafa',
        paper_bgcolor: '#ffffff'
    };
    
    const config = {
        responsive: true,
        displayModeBar: false  // PIMS와 동일하게 툴바 숨기기
    };
    
    Plotly.newPlot('cvChart1', [trace], layout, config);
}

// ========================================
// 9. 유틸리티 함수들
// ========================================
function showLimsLoading(show) {
    const button = document.getElementById('searchBtnStats');
    if (button) {
        if (show) {
            button.disabled = true;
            button.innerHTML = '<span class="lims-loading me-2"></span>조회 중...';
        } else {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-flask me-1"></i>실험결과 조회';
        }
    }
}

function showResultContainer() {
    const container = document.getElementById('resultContainerStats');
    if (container) {
        container.style.display = 'block';
    }
}

function hideResultContainer() {
    const container = document.getElementById('resultContainerStats');
    if (container) {
        container.style.display = 'none';
    }
}

function showLimsInfo(dataCount, batchCount) {
    console.log(`📊 LIMS 조회 완료: ${dataCount}건 (${batchCount}개 배치)`);
    
    // 성공 알림 표시
    showSuccessAlert(`LIMS 실험결과 조회 완료: ${dataCount}건 (${batchCount}개 배치)`);
}

function showErrorAlert(message) {
    // 간단한 Bootstrap 알림 표시
    console.error('❌', message);
    alert('오류: ' + message);
}

function showInfoAlert(message) {
    console.log('ℹ️', message);
    alert('알림: ' + message);
}

function showSuccessAlert(message) {
    console.log('✅', message);
    // 성공 메시지는 콘솔에만 표시 (사용자에게는 표시하지 않음)
}

// CSV 다운로드 함수
function downloadAllLimsDataAsCSV() {
    if (!currentLimsChartData || currentLimsChartData.length === 0) {
        showErrorAlert('다운로드할 데이터가 없습니다.');
        return;
    }
    
    const csvContent = convertToCSV(currentLimsChartData);
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `LIMS_실험결과_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadCvResults() {
    if (!currentLimsChartData || currentLimsChartData.length === 0) {
        showErrorAlert('CV 분석 결과를 다운로드할 데이터가 없습니다.');
        return;
    }
    
    console.log('LIMS CV 결과 다운로드 - 실험항목별 CV 계산');
    
    // 차트와 동일한 로직으로 실험항목별 CV 계산
    const analyteGroups = {};
    currentLimsChartData.forEach(row => {
        const analyte = row.ANALYTE;
        const finalValue = row.FINAL;
        const batch = row.CHARG || 'Unknown';
        
        if (analyte && finalValue && isNumericValue(finalValue)) {
            if (!analyteGroups[analyte]) {
                analyteGroups[analyte] = {
                    values: [],
                    batches: []
                };
            }
            analyteGroups[analyte].values.push(parseFloat(finalValue));
            analyteGroups[analyte].batches.push(batch);
        }
    });
    
    // 실험항목별 CV 결과 생성
    const cvResults = [];
    Object.keys(analyteGroups).sort().forEach(analyte => {
        const data = analyteGroups[analyte];
        const values = data.values;
        const batches = data.batches;
        
        if (values.length >= 2) {
            // CV 계산
            const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
            const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (values.length - 1);
            const std = Math.sqrt(variance);
            
            let cv = 0;
            let stability = '데이터 부족';
            
            if (mean !== 0) {
                cv = (std / Math.abs(mean)) * 100;
                
                // 안정성 평가
                if (cv < 5) {
                    stability = '안정';
                } else if (cv < 15) {
                    stability = '보통';
                } else {
                    stability = '위험';
                }
            }
            
            cvResults.push({
                '실험항목': analyte,
                '데이터수': values.length,
                '평균': mean.toFixed(3),
                '표준편차': std.toFixed(3),
                'CV(%)': cv.toFixed(2),
                '안정성평가': stability,
                '최소값': Math.min(...values).toFixed(3),
                '최대값': Math.max(...values).toFixed(3)
            });
        } else if (values.length === 1) {
            // 값이 1개만 있는 경우
            cvResults.push({
                '실험항목': analyte,
                '데이터수': 1,
                '평균': values[0].toFixed(3),
                '표준편차': '0.000',
                'CV(%)': '0.00',
                '안정성평가': '데이터 부족',
                '최소값': values[0].toFixed(3),
                '최대값': values[0].toFixed(3)
            });
        }
    });
    
    if (cvResults.length === 0) {
        showErrorAlert('CV 계산 가능한 실험항목이 없습니다.');
        return;
    }
    
    const csvContent = convertToCSV(cvResults);
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `LIMS_실험항목별_CV분석결과_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log(`✅ CV 분석 결과 다운로드 완료: ${cvResults.length}개 실험항목`);
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [];
    
    // 헤더 추가
    csvRows.push(headers.join(','));
    
    // 데이터 행 추가
    data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header];
            if (value === null || value === undefined) return '';
            return typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value;
        });
        csvRows.push(values.join(','));
    });
    
    return csvRows.join('\n');
}

// Debounce 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
} 