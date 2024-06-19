from deep_sort_realtime.deepsort_tracker import DeepSort

class DeepSortWrapper:
  def __init__(self, max_age, n_init):
    self.tracker = DeepSort(max_age= max_age, n_init= n_init)

  def update_tracker(self, detections, frame):
    tracks = self.tracker.update_tracks(detections, frame=frame)
    return tracks