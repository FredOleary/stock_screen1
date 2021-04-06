import pandas as pd
import numpy as np
from DbFinance import FinanceDB
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn

from ForecastLSTM import ForecastLSTM
from pathlib import Path

"""
SAMPLES_PER_DAY:
With a sample period of about 15 min and 6.5 hrs in a trading period, that translates to
about 6*4 + 2, (26 samples). Since collection is 'approximate' limit the samples of each day,
discarding the earlier measurements. (TODO refactor the collector to to a better job!)
"""
SAMPLES_PER_DAY = 24

TEST_DATA_SIZE = 24

TRAIN_WINDOW = 24

FUTURE_COUNT = 48


class Prediction:
    def __init__(self,
                 db: FinanceDB,
                 symbol: str,
                 expiration_key: int,
                 expiration: pd.Timestamp,
                 strike: float,
                 put_call: str,
                 metric: str,
                 training_event,
                 logger=None, ):
        self.symbol = symbol
        self.db = db
        self.expiration_key = expiration_key
        self.strike = strike
        self.put_call = put_call
        self.metric = metric
        self.logger = logger
        self.train_data_normalized = None
        self.expiration = expiration
        self.scaler = None
        self.training_event = training_event

    def calculate_predictions(self):
        df = self.__load_series_from_db()
        day_list = self.__process_to_days(df)
        day_ndarray = self.__process_day_list(day_list)
        if len(day_ndarray) > 0:
            train_data_normalized = self.__train_data(day_ndarray, TEST_DATA_SIZE)
            self.__train_or_load_model(train_data_normalized)
            last_day_predictions, next_day_predictions = self.__create_predictions(FUTURE_COUNT)
            return last_day_predictions, next_day_predictions
        else:
            return None, None

    def __load_series_from_db(self) -> pd.DataFrame:
        df = self.db.get_strike_data_for_expiration(self.expiration_key, self.strike, self.put_call)
        return df

    def __process_to_days(self, df: pd.DataFrame) -> list:
        result = []
        i = 0;
        end = len(df)
        while i < end:
            day = df.iloc[i]["time"].day
            day_list = [df.iloc[i][self.metric]]
            result.append(day_list)
            i = i + 1
            while i < len(df):
                next_day = (df.iloc[i])["time"].day
                if next_day == day:
                    day_list.append(df.iloc[i][self.metric])
                    i += 1
                else:
                    break
        # for day in result:
        #     print(len(day))
        return result

    def __process_day_list(self, day_list: list) -> np.ndarray:
        """
        process the samples to have the same number of samples in each day
        with a sample period of about 15 min and 6.5 hrs in a trading period, that translates to
        about 6*4 + 2, (26 samples). Since collection is 'approximate' limit the samples of each day,
        discarding the later measurements. (TODO refactor the collector to to a better job!)
        """
        output = []
        for day in day_list:
            if len(day) >= SAMPLES_PER_DAY:
                output.append(day[-SAMPLES_PER_DAY:])
        return np.asarray(output).flatten()

    def __train_data(self, day_ndarray: np.ndarray, test_data_size) -> (np.ndarray, np.ndarray):
        train_data = day_ndarray[:-test_data_size]
        # test_data = day_ndarray[-test_data_size:]

        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        train_data_normalized = self.scaler.fit_transform(train_data.reshape(-1, 1))
        return train_data_normalized

    def __train_or_load_model(self, td_normalized: np.ndarray):

        self.train_data_normalized = torch.FloatTensor(td_normalized).view(-1)

        train_inout_seq = self.__create_inout_sequences(self.train_data_normalized, TRAIN_WINDOW)

        self.model = ForecastLSTM()
        saved_trained_model = f"{self.symbol}-{self.strike}-{self.expiration.strftime('%Y-%m-%d')}.pt"

        my_file = Path(saved_trained_model)
        if my_file.is_file():
            self.model.load_state_dict(torch.load(saved_trained_model))
        else:
            print(f"Beginning training")
            self.training_event(f"Beginning training")
            loss_function = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            epochs = 150

            for i in range(epochs):
                for seq, labels in train_inout_seq:
                    optimizer.zero_grad()
                    self.model.hidden_cell = (torch.zeros(1, 1, self.model.hidden_layer_size),
                                              torch.zeros(1, 1, self.model.hidden_layer_size))

                    y_pred = self.model(seq)

                    single_loss = loss_function(y_pred, labels)
                    single_loss.backward()
                    optimizer.step()
                self.training_event(f"epoch {i}")
                if i % 5 == 1:
                    print(f'Epoch: {i:3} loss: {single_loss.item():10.8f}')

            print(f"Training complete")
            self.training_event(f"Training complete")
            torch.save(self.model.state_dict(), saved_trained_model)
        self.test_inputs = self.train_data_normalized[-TRAIN_WINDOW:].tolist()
        self.model.eval()

    def __create_inout_sequences(self, input_data, tw):
        inout_seq = []
        L = len(input_data)
        for i in range(L - tw):
            train_seq = input_data[i:i + tw]
            train_label = input_data[i + tw:i + tw + 1]
            inout_seq.append((train_seq, train_label))
        return inout_seq

    def __create_predictions(self, prediction_count: int):
        for i in range(prediction_count):
            seq = torch.FloatTensor(self.test_inputs[-TRAIN_WINDOW:])
            with torch.no_grad():
                self.model.hidden = (torch.zeros(1, 1, self.model.hidden_layer_size),
                                     torch.zeros(1, 1, self.model.hidden_layer_size))
                self.test_inputs.append(self.model(seq).item())

        actual_predictions = self.scaler.inverse_transform(np.array(self.test_inputs[TEST_DATA_SIZE:]).reshape(-1, 1))
        last_day_predictions = actual_predictions[:TEST_DATA_SIZE]
        next_day_predictions = actual_predictions[TEST_DATA_SIZE:]
        return last_day_predictions, next_day_predictions
