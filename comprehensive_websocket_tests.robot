*** Settings ***
Documentation    Comprehensive WebSocket AsyncAPI Test Suite
...              This test suite covers all critical aspects of WebSocket testing including:
...              - Connection management and reliability
...              - Message ordering and race conditions  
...              - High-frequency messaging and performance
...              - Error handling and recovery scenarios
...              - Concurrent operations and thread safety
...              - Network failure simulation and auto-reconnect
...              - Security and authentication scenarios
...              - Resource cleanup and memory management

Library          ../ModernAsyncAPILibrary.py
Library          Collections
Library          DateTime
Library          OperatingSystem
Library          Process

Suite Setup      Setup Test Environment
Suite Teardown   Teardown Test Environment
Test Setup       Setup Individual Test
Test Teardown    Cleanup Individual Test

*** Variables ***
${GPIO_SERVER_URL}           wss://127.0.0.1:8080
${INVALID_SERVER_URL}        wss://invalid-server:9999
${TIMEOUT_SHORT}             5
${TIMEOUT_MEDIUM}            15
${TIMEOUT_LONG}              30
${HIGH_FREQUENCY_COUNT}      100
${RACE_CONDITION_COUNT}      50
${PERFORMANCE_THRESHOLD}     10    # messages per second minimum

*** Test Cases ***

# =============================================================================
# CONNECTION MANAGEMENT TESTS
# =============================================================================

Test Basic Connection Lifecycle
    [Documentation]    Test basic connection establishment and cleanup
    [Tags]    connection    basic    smoke
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Should Be Disconnected
    
    Connect To WebSocket Server
    Should Be Connected
    
    Disconnect From WebSocket Server
    Should Be Disconnected

Test Connection With Auto Reconnect
    [Documentation]    Test connection with auto-reconnect enabled
    [Tags]    connection    reconnect    reliability
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server    auto_reconnect=${True}    timeout=${TIMEOUT_MEDIUM}
    Should Be Connected
    
    # Verify connection remains stable
    Sleep    3s
    Should Be Connected

Test Connection Timeout Handling
    [Documentation]    Test connection timeout with invalid server
    [Tags]    connection    timeout    error
    
    Initialize GPIO Client    ${INVALID_SERVER_URL}
    
    Run Keyword And Expect Error
    ...    Connection timed out after * seconds
    ...    Connect To WebSocket Server    timeout=${TIMEOUT_SHORT}
    
    Should Be Disconnected

Test Multiple Connection Attempts
    [Documentation]    Test multiple rapid connection attempts
    [Tags]    connection    stress    race
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    
    # First connection should succeed
    Connect To WebSocket Server
    Should Be Connected
    
    # Second connection attempt should handle gracefully
    Connect To WebSocket Server
    Should Be Connected
    
    # Verify only one connection is active
    ${message_count_before}=    Get Message Count
    Send GPIO High
    Wait For GPIO Message    timeout=${TIMEOUT_SHORT}
    ${message_count_after}=    Get Message Count
    ${received_count}=    Evaluate    ${message_count_after} - ${message_count_before}
    Should Be Equal As Integers    ${received_count}    1

# =============================================================================
# MESSAGE ORDERING AND RACE CONDITION TESTS  
# =============================================================================

Test Sequential Message Ordering
    [Documentation]    Test that messages are received in the order sent
    [Tags]    messaging    ordering    sequential
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Clear Received Messages
    
    # Send sequence of alternating GPIO commands
    FOR    ${i}    IN RANGE    10
        ${status}=    Set Variable If    ${i} % 2 == 0    high    low
        Send GPIO Message    {"status": "${status}", "sequence": ${i}}
        Sleep    0.1s    # Small delay to ensure ordering
    END
    
    # Wait for all responses
    Wait For Multiple WebSocket Messages    10    timeout=${TIMEOUT_MEDIUM}
    
    # Verify sequence numbers are in order
    ${gpio_messages}=    Get GPIO Messages
    ${length}=    Get Length    ${gpio_messages}
    Should Be Equal As Integers    ${length}    10
    
    FOR    ${i}    IN RANGE    10
        ${message}=    Get From List    ${gpio_messages}    ${i}
        ${payload}=    Get From Dictionary    ${message}    payload
        ${sequence}=    Get From Dictionary    ${payload}    sequence
        Should Be Equal As Integers    ${sequence}    ${i}
    END

Test Rapid Fire Message Race Conditions
    [Documentation]    Test sending many messages rapidly to check for race conditions
    [Tags]    messaging    race    performance    stress
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Clear Received Messages
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    # Send messages as fast as possible
    FOR    ${i}    IN RANGE    ${RACE_CONDITION_COUNT}
        ${status}=    Set Variable If    ${i} % 2 == 0    high    low
        Send GPIO Message    {"status": "${status}", "id": ${i}}
        # No delay - testing race conditions
    END
    
    ${send_time}=    Get Current Date    result_format=epoch
    ${send_duration}=    Evaluate    ${send_time} - ${start_time}
    Log    Sent ${RACE_CONDITION_COUNT} messages in ${send_duration} seconds
    
    # Wait for all responses with generous timeout
    Wait For Multiple WebSocket Messages    ${RACE_CONDITION_COUNT}    timeout=${TIMEOUT_LONG}
    
    ${end_time}=    Get Current Date    result_format=epoch
    ${total_duration}=    Evaluate    ${end_time} - ${start_time}
    ${throughput}=    Evaluate    ${RACE_CONDITION_COUNT} / ${total_duration}
    
    Log    Total test duration: ${total_duration} seconds
    Log    Throughput: ${throughput} messages/second
    
    # Verify all messages were received
    ${gpio_messages}=    Get GPIO Messages
    ${received_count}=    Get Length    ${gpio_messages}
    Should Be Equal As Integers    ${received_count}    ${RACE_CONDITION_COUNT}
    
    # Verify no messages were lost or duplicated
    ${message_ids}=    Create List
    FOR    ${message}    IN    @{gpio_messages}
        ${payload}=    Get From Dictionary    ${message}    payload
        ${msg_id}=    Get From Dictionary    ${payload}    id
        Append To List    ${message_ids}    ${msg_id}
    END
    
    ${unique_ids}=    Remove Duplicates    ${message_ids}
    ${unique_count}=    Get Length    ${unique_ids}
    Should Be Equal As Integers    ${unique_count}    ${RACE_CONDITION_COUNT}

Test Concurrent Bidirectional Communication
    [Documentation]    Test simultaneous sending and receiving
    [Tags]    messaging    concurrent    bidirectional
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Clear Received Messages
    
    # Start rapid sending in background while monitoring responses
    FOR    ${batch}    IN RANGE    5
        # Send a batch of messages
        FOR    ${i}    IN RANGE    10
            ${msg_id}=    Evaluate    ${batch} * 10 + ${i}
            Send GPIO Message    {"status": "high", "batch": ${batch}, "id": ${msg_id}}
        END
        
        # Immediately check for any responses that came in
        ${current_count}=    Get Message Count
        Log    After batch ${batch}: ${current_count} messages received
        
        # Small delay before next batch
        Sleep    0.2s
    END
    
    # Wait for all responses
    Wait For Multiple WebSocket Messages    50    timeout=${TIMEOUT_LONG}
    
    # Verify batching didn't cause message loss
    ${gpio_messages}=    Get GPIO Messages
    ${final_count}=    Get Length    ${gpio_messages}
    Should Be Equal As Integers    ${final_count}    50

# =============================================================================
# HIGH-FREQUENCY AND PERFORMANCE TESTS
# =============================================================================

Test High Frequency GPIO Commands
    [Documentation]    Test system under high message frequency
    [Tags]    performance    high-frequency    stress
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Clear Received Messages
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    # Send high-frequency GPIO commands
    FOR    ${i}    IN RANGE    ${HIGH_FREQUENCY_COUNT}
        ${status}=    Set Variable If    ${i} % 2 == 0    high    low
        Send GPIO Message    {"status": "${status}", "freq_test": ${i}}
    END
    
    ${send_end_time}=    Get Current Date    result_format=epoch
    ${send_duration}=    Evaluate    ${send_end_time} - ${start_time}
    ${send_rate}=    Evaluate    ${HIGH_FREQUENCY_COUNT} / ${send_duration}
    
    Log    Send rate: ${send_rate} messages/second
    Should Be True    ${send_rate} >= ${PERFORMANCE_THRESHOLD}
    
    # Wait for all responses
    Wait For Multiple WebSocket Messages    ${HIGH_FREQUENCY_COUNT}    timeout=${TIMEOUT_LONG}
    
    ${end_time}=    Get Current Date    result_format=epoch
    ${total_duration}=    Evaluate    ${end_time} - ${start_time}
    ${overall_rate}=    Evaluate    ${HIGH_FREQUENCY_COUNT} / ${total_duration}
    
    Log    Overall rate: ${overall_rate} messages/second
    Should Be True    ${overall_rate} >= ${PERFORMANCE_THRESHOLD}

Test Message Throughput Limits
    [Documentation]    Find the throughput limits of the WebSocket connection
    [Tags]    performance    limits    benchmark
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    
    # Test different batch sizes to find optimal throughput
    @{batch_sizes}=    Create List    10    25    50    100
    @{throughputs}=    Create List
    
    FOR    ${batch_size}    IN    @{batch_sizes}
        Clear Received Messages
        
        ${start_time}=    Get Current Date    result_format=epoch
        
        FOR    ${i}    IN RANGE    ${batch_size}
            Send GPIO High
        END
        
        Wait For Multiple WebSocket Messages    ${batch_size}    timeout=${TIMEOUT_LONG}
        
        ${end_time}=    Get Current Date    result_format=epoch
        ${duration}=    Evaluate    ${end_time} - ${start_time}
        ${throughput}=    Evaluate    ${batch_size} / ${duration}
        
        Append To List    ${throughputs}    ${throughput}
        Log    Batch size ${batch_size}: ${throughput} messages/second
    END
    
    # Log throughput analysis
    ${max_throughput}=    Evaluate    max(${throughputs})
    Log    Maximum observed throughput: ${max_throughput} messages/second

# =============================================================================
# ERROR HANDLING AND RECOVERY TESTS
# =============================================================================

Test Connection Recovery After Network Error
    [Documentation]    Test recovery from network-level connection issues
    [Tags]    error    recovery    network    reconnect
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server    auto_reconnect=${True}
    Should Be Connected
    
    # Send a message to confirm working connection
    Send GPIO High
    Wait For GPIO Message    timeout=${TIMEOUT_SHORT}
    
    # TODO: Simulate network interruption (requires mock server support)
    # For now, test disconnection and manual reconnection
    Disconnect From WebSocket Server
    Should Be Disconnected
    
    # Reconnect and verify functionality
    Connect To WebSocket Server    auto_reconnect=${True}
    Should Be Connected
    
    # Verify connection works after recovery
    Send GPIO Low
    Wait For GPIO Status    low    timeout=${TIMEOUT_SHORT}

Test Invalid Message Handling
    [Documentation]    Test handling of malformed or invalid messages
    [Tags]    error    invalid    robustness
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Clear Received Messages
    
    # Test various invalid message scenarios
    
    # Invalid JSON
    Run Keyword And Continue On Failure
    ...    Send Raw Message    {invalid json}
    
    # Missing required fields
    Run Keyword And Continue On Failure
    ...    Send Custom Message    {"type": "GpioMessage"}
    
    # Invalid GPIO status
    Run Keyword And Continue On Failure
    ...    Send GPIO Message    {"status": "invalid"}
    
    # Verify connection is still working after invalid messages
    Send GPIO High
    Wait For GPIO Status    high    timeout=${TIMEOUT_SHORT}

Test Error Handler Registration
    [Documentation]    Test that error handlers are properly registered and called
    [Tags]    error    handlers    callbacks
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    
    # Clear any previous errors
    Clear Last Error
    ${error}=    Get Last Error
    Should Be Equal    ${error}    ${None}
    
    # Trigger an error condition (disconnect and try to send)
    Disconnect From WebSocket Server
    
    # Attempt to send message while disconnected (should trigger error)
    Run Keyword And Expect Error
    ...    *
    ...    Send GPIO High
    
    # Note: Error handling testing is limited without mock server that can inject errors

# =============================================================================
# CONCURRENT OPERATIONS AND THREAD SAFETY TESTS
# =============================================================================

Test Multiple Simultaneous Operations  
    [Documentation]    Test thread safety with multiple concurrent operations
    [Tags]    concurrent    thread-safety    parallel
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Clear Received Messages
    
    # Simulate concurrent operations by rapidly switching between different activities
    FOR    ${round}    IN RANGE    10
        # Mixed operations in rapid succession
        Send GPIO High
        ${count1}=    Get Message Count
        Send GPIO Low
        ${count2}=    Get Message Count
        Send GPIO Message    {"status": "high", "round": ${round}}
        ${count3}=    Get Message Count
        
        # Verify counts are increasing (messages being received)
        Should Be True    ${count2} >= ${count1}
        Should Be True    ${count3} >= ${count2}
    END
    
    # Wait for all messages to arrive
    Wait For Multiple WebSocket Messages    30    timeout=${TIMEOUT_LONG}

Test Connection State Consistency
    [Documentation]    Test connection state remains consistent under rapid state changes
    [Tags]    concurrent    state    consistency
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    
    # Test rapid connection state changes
    FOR    ${i}    IN RANGE    5
        Connect To WebSocket Server
        Should Be Connected
        
        # Send message to verify connection works
        Send GPIO High
        
        Disconnect From WebSocket Server  
        Should Be Disconnected
        
        # Verify we can't send while disconnected
        Run Keyword And Expect Error
        ...    *
        ...    Send GPIO Low
    END

# =============================================================================
# NETWORK FAILURE SIMULATION TESTS
# =============================================================================

Test Connection Timeout Scenarios
    [Documentation]    Test various timeout scenarios
    [Tags]    timeout    network    reliability
    
    # Test connection timeout
    Initialize GPIO Client    ${INVALID_SERVER_URL}
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    Run Keyword And Expect Error
    ...    Connection timed out after * seconds
    ...    Connect To WebSocket Server    timeout=3
    
    ${end_time}=    Get Current Date    result_format=epoch
    ${actual_duration}=    Evaluate    ${end_time} - ${start_time}
    
    # Verify timeout was approximately correct (allow some variance)
    Should Be True    ${actual_duration} >= 2.5
    Should Be True    ${actual_duration} <= 4.0

Test Message Timeout Scenarios
    [Documentation]    Test message waiting timeout scenarios
    [Tags]    timeout    messaging    error
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    Clear Received Messages
    
    # Test waiting for message that will never come
    ${start_time}=    Get Current Date    result_format=epoch
    
    Run Keyword And Expect Error
    ...    Message 'NonExistentMessage' not received within * seconds
    ...    Wait For WebSocket Message    NonExistentMessage    timeout=3
    
    ${end_time}=    Get Current Date    result_format=epoch
    ${actual_duration}=    Evaluate    ${end_time} - ${start_time}
    
    # Verify timeout was approximately correct
    Should Be True    ${actual_duration} >= 2.5
    Should Be True    ${actual_duration} <= 4.0

# =============================================================================
# RESOURCE CLEANUP AND MEMORY MANAGEMENT TESTS
# =============================================================================

Test Resource Cleanup After Multiple Connections
    [Documentation]    Test proper cleanup after multiple connection cycles
    [Tags]    cleanup    resources    memory
    
    # Multiple connection/disconnection cycles
    FOR    ${cycle}    IN RANGE    5
        Initialize GPIO Client    ${GPIO_SERVER_URL}
        Connect To WebSocket Server
        
        # Send some messages to create activity
        Send GPIO High
        Send GPIO Low
        Wait For Multiple WebSocket Messages    2    timeout=${TIMEOUT_SHORT}
        
        # Cleanup this cycle
        Cleanup AsyncAPI Client
        
        # Brief pause between cycles
        Sleep    0.5s
    END

Test Memory Usage With High Message Volume
    [Documentation]    Test memory doesn't grow excessively with high message volume
    [Tags]    memory    performance    cleanup
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server
    
    # Generate high message volume and monitor buffer size
    FOR    ${batch}    IN RANGE    10
        Clear Received Messages
        
        # Send batch of messages
        FOR    ${i}    IN RANGE    20
            Send GPIO Message    {"status": "high", "batch": ${batch}, "msg": ${i}}
        END
        
        # Wait for responses
        Wait For Multiple WebSocket Messages    20    timeout=${TIMEOUT_MEDIUM}
        
        # Check message buffer size
        ${buffer_size}=    Get Message Count
        Log    Batch ${batch}: Buffer contains ${buffer_size} messages
        
        # Buffer should not grow excessively
        Should Be True    ${buffer_size} <= 50
    END

# =============================================================================
# SECURITY AND AUTHENTICATION TESTS
# =============================================================================

Test SSL/TLS Connection
    [Documentation]    Test secure WebSocket connections (WSS)
    [Tags]    security    ssl    tls
    
    # Test with wss:// URL (secure WebSocket)
    Initialize GPIO Client    wss://127.0.0.1:8080
    
    # Should connect successfully with SSL/TLS
    Connect To WebSocket Server    timeout=${TIMEOUT_MEDIUM}
    Should Be Connected
    
    # Verify encrypted connection works for messaging
    Send GPIO High
    Wait For GPIO Status    high    timeout=${TIMEOUT_SHORT}

Test Connection With Invalid Certificates
    [Documentation]    Test behavior with certificate issues
    [Tags]    security    certificates    error
    
    # Note: This test requires a server with invalid certificates
    # For demonstration, we test connection to non-existent SSL server
    Initialize GPIO Client    wss://invalid-ssl-server:8080
    
    Run Keyword And Expect Error
    ...    *
    ...    Connect To WebSocket Server    timeout=${TIMEOUT_SHORT}

# =============================================================================
# INTEGRATION AND END-TO-END TESTS  
# =============================================================================

Test Complete GPIO Control Workflow
    [Documentation]    Test a complete realistic GPIO control workflow
    [Tags]    integration    workflow    e2e
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server    auto_reconnect=${True}
    Clear Received Messages
    
    # Simulate real GPIO control sequence
    Log    Starting GPIO control sequence
    
    # Initialize - Set all pins low
    Send GPIO Message    {"status": "low", "pin": "all", "action": "initialize"}
    Wait For GPIO Status    low    timeout=${TIMEOUT_SHORT}
    
    # Activation sequence
    FOR    ${pin}    IN RANGE    1    5
        Log    Activating GPIO pin ${pin}
        Send GPIO Message    {"status": "high", "pin": ${pin}, "action": "activate"}
        Wait For GPIO Status    high    timeout=${TIMEOUT_SHORT}
        Sleep    0.5s    # Realistic delay
    END
    
    # Status check
    Send GPIO Message    {"action": "status_check"}
    Wait For GPIO Message    timeout=${TIMEOUT_SHORT}
    
    # Deactivation sequence
    FOR    ${pin}    IN RANGE    4    0    -1    # Reverse order
        Log    Deactivating GPIO pin ${pin}
        Send GPIO Message    {"status": "low", "pin": ${pin}, "action": "deactivate"}
        Wait For GPIO Status    low    timeout=${TIMEOUT_SHORT}
        Sleep    0.5s
    END
    
    # Final status verification
    ${gpio_messages}=    Get GPIO Messages
    ${total_messages}=    Get Length    ${gpio_messages}
    Should Be True    ${total_messages} >= 10    # Should have received multiple status updates
    
    Log    GPIO control workflow completed successfully

Test System Under Full Load
    [Documentation]    Comprehensive system test under maximum load
    [Tags]    integration    stress    full-load
    
    Initialize GPIO Client    ${GPIO_SERVER_URL}
    Connect To WebSocket Server    auto_reconnect=${True}
    
    ${start_time}=    Get Current Date    result_format=epoch
    
    # Multiple concurrent activities
    FOR    ${phase}    IN RANGE    3
        Clear Received Messages
        
        # Rapid GPIO commands
        FOR    ${i}    IN RANGE    30
            ${status}=    Set Variable If    ${i} % 2 == 0    high    low
            Send GPIO Message    {"status": "${status}", "phase": ${phase}, "cmd": ${i}}
        END
        
        # Mixed message types
        Send Raw Message    {"type": "GpioMessage", "payload": {"status": "high", "raw": true}}
        Send Custom Message    {"type": "GpioMessage", "payload": {"status": "low", "custom": true}}
        
        # Wait for all responses from this phase
        Wait For Multiple WebSocket Messages    32    timeout=${TIMEOUT_LONG}
        
        Log    Completed phase ${phase}
    END
    
    ${end_time}=    Get Current Date    result_format=epoch
    ${total_duration}=    Evaluate    ${end_time} - ${start_time}
    ${total_messages}=    Evaluate    3 * 32    # 32 messages per phase, 3 phases
    ${overall_throughput}=    Evaluate    ${total_messages} / ${total_duration}
    
    Log    Full load test: ${total_messages} messages in ${total_duration} seconds
    Log    Overall throughput: ${overall_throughput} messages/second
    
    # Verify system maintained performance under load
    Should Be True    ${overall_throughput} >= ${PERFORMANCE_THRESHOLD}

*** Keywords ***

Setup Test Environment
    [Documentation]    Set up the test environment
    Log    Setting up WebSocket AsyncAPI test environment
    
    # TODO: Start mock GPIO server if needed
    # ${result}=    Start Process    python    mock_gpio_server.py    
    # Set Test Variable    ${MOCK_SERVER_PROCESS}    ${result}
    
    Log    Test environment ready

Teardown Test Environment
    [Documentation]    Clean up the test environment
    Log    Tearing down test environment
    
    # TODO: Stop mock server if started
    # Run Keyword If    '${MOCK_SERVER_PROCESS}' != '${EMPTY}'
    # ...    Terminate Process    ${MOCK_SERVER_PROCESS}
    
    Log    Test environment cleaned up

Setup Individual Test
    [Documentation]    Set up for individual test case
    Log    Setting up individual test case
    # Individual test setup can be added here if needed

Cleanup Individual Test  
    [Documentation]    Clean up after individual test case
    Log    Cleaning up individual test case
    
    # Always ensure client is cleaned up after each test
    Run Keyword And Ignore Error    Cleanup AsyncAPI Client
    
    # Small delay to ensure cleanup is complete
    Sleep    0.1s

Remove Duplicates
    [Documentation]    Remove duplicate values from a list
    [Arguments]    ${input_list}
    
    ${unique_list}=    Create List
    FOR    ${item}    IN    @{input_list}
        ${contains}=    Run Keyword And Return Status    List Should Contain Value    ${unique_list}    ${item}
        Run Keyword If    not ${contains}    Append To List    ${unique_list}    ${item}
    END
    
    RETURN    ${unique_list}