class DoesNotMeetRequirements(Exception):
	def __init__(self, msg, available):
		super(Exception, self).__init__(msg)
		self.msg = msg
		self.available = available