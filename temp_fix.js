/**
 * 통계 분석용 드롭다운 업데이트 (PIMS 버전 - 수정됨)
 */
function updateStatsVariableDropdown(data) {
    console.log('통계 드롭다운 업데이트 시작:', data?.length, '개 데이터');
    
    const select = document.getElementById('statsVariableSelect');
    if (!select) {
        console.error('statsVariableSelect 요소를 찾을 수 없습니다!');
        return;
    }
    
    if (!data || data.length === 0) {
        console.log('데이터가 비어있습니다.');
        select.innerHTML = '<option value="">데이터가 없습니다</option>';
        return;
    }
    
    // 기존 옵션 제거
    select.innerHTML = '<option value="">변수를 선택하세요</option>';
    
    // 첫 번째 데이터 행에서 열 이름들 가져오기
    const firstRow = data[0];
    const excludeKeys = ['배치번호', '품목코드', '공정코드', 'batchNo', 'batch'];
    
    // 제외할 키들을 뺀 모든 키들을 변수로 처리 (PIMS는 모든 데이터가 숫자이므로 간소화)
    const variables = Object.keys(firstRow).filter(key => {
        const keyLower = key.toLowerCase();
        return !excludeKeys.includes(key) && 
               !keyLower.includes('time') && 
               !keyLower.includes('timestamp') &&
               !keyLower.includes('batch');
    });
    
    console.log('발견된 변수들:', variables);
    
    // 변수들을 정렬하여 옵션 추가
    variables.sort().forEach(variable => {
        const option = document.createElement('option');
        option.value = variable;
        option.textContent = variable;
        select.appendChild(option);
    });
    
    console.log(`✅ PIMS 통계 분석용 드롭다운 업데이트 완료: ${variables.length}개 항목`);
    
    if (variables.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '사용 가능한 변수가 없습니다';
        select.appendChild(option);
    } else {
        // 첫 번째 변수를 자동 선택하고 즉시 통계 표시
        const firstVariable = variables[0];
        select.value = firstVariable;
        
        console.log('✅ 첫 번째 변수 자동 선택:', firstVariable);
        
        // 즉시 통계 분석 업데이트
        setTimeout(() => {
            updateStatsAnalysis();
        }, 100);
    }
    
    // 이벤트 리스너 등록
    select.removeEventListener('change', updateStatsAnalysis);
    select.addEventListener('change', updateStatsAnalysis);
    
    console.log('✅ 드롭다운 이벤트 리스너 등록 완료');
}