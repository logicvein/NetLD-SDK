from jsonrpc import JsonRpcProxy, JsonError

class NetLdUtils
   '''A utility class with miscellaneous functions'''

   def __init__(self, netldService):
      self._netld_svc = netldService

   def wait_for_completion(self, execution):
      execution_id = execution['id']

      # wait for completion
      while (execution['endTime'] is None):
         state = execution['completionState']
         if (state == 1 or state == 2):
            print "FAILED $state"

         # wait one second so that we don't spam the server
         time.sleep(1)

         execution = self._netld_svc.call('Scheduler.getExecutionDataById', execution_id)

      return execution
