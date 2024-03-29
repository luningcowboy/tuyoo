# -*- coding:utf-8 -*-
"""
Created on 2017年2月15日

@author: zhaojiangang
"""
from dizhu.entity.dizhuconf import DIZHU_GAMEID
from dizhu.games.normalbase.tableproto import DizhuTableProtoNormalBase
from dizhu.games.tablecommonproto import DizhuTableProtoCommonBase
from dizhu.servers.util.rpc import task_remote, new_table_remote
from poker.entity.configure import configure
from poker.entity.dao import gamedata
from poker.protocol import router
from dizhucomm.entity import commconf
import freetime.util.log as ftlog
from poker.util import strutil


class DizhuTableProtoSegment(DizhuTableProtoNormalBase):
    def __init__(self, tableCtrl):
        super(DizhuTableProtoSegment, self).__init__(tableCtrl)

    def buildTableInfoResp(self, seat, isRobot):
        mp = DizhuTableProtoCommonBase.buildTableInfoResp(self, seat, isRobot)
        winStreakInfo = task_remote.doSegmentTableWinStreakTask(seat.userId)
        mp.setResult('winStreakInfo', winStreakInfo)
        dailyPlayCount = new_table_remote.doGetUserDailyPlayCount(seat.userId, DIZHU_GAMEID)
        mp.setResult('dailyPlay', dailyPlayCount)
        return mp

    # 天梯赛桌重写QuickStart消息
    def buildQuickStartResp(self, seat, isOK, reason):
        mp = self.buildTableMsgRes('quick_start')
        mp.setResult('isOK', isOK)
        mp.setResult('seatId', seat.seatId)
        mp.setResult('reason', reason)
        mp.setResult('tableType', 'segment')
        return mp

    def buildResultDetails(self, result):
        winStreak = []
        cards = []
        addCoupons = []
        seatDetails = []
        seatInfos = []
        segmentInfos = []
        recoverInfos = []
        rewardInfos = []
        winStreakRewardInfos = []
        treasureChestInfos = []
        for sst in result.seatStatements:
            waittime = self.table.runConf.optimeCall
            if sst.final < self.table.runConf.minCoin:
                waittime = int(waittime / 3)

            details = [
                sst.delta,
                sst.final,
                0,
                waittime,
                0,
                0,
                sst.expInfo[0], sst.expInfo[1], sst.expInfo[2], sst.expInfo[3], sst.expInfo[4],
                sst.seat.player.chip
            ]

            seatDetails.append(details)
            winStreak.append(sst.winStreak)
            cards.append(sst.seat.status.cards)
            addCoupons.append(0)
            seatInfos.append({'punished': 1} if sst.isPunish else {})
            segmentInfos.append(sst.segmentInfo)
            rewardInfos.append(sst.rewardInfo)
            recoverInfos.append(sst.recoverInfo)
            winStreakRewardInfos.append(sst.winStreakRewardInfo)
            treasureChestInfos.append(sst.treasureChestInfo)
            sst.seat.player.playShare.lastChip = sst.seat.player.score
            sst.seat.player.playShare.maxWinDoubles = max(sst.seat.player.playShare.maxWinDoubles, sst.totalMulti)

        return {
            'winStreak': winStreak,
            'addcoupons': addCoupons,
            'cards': cards,
            'seatDetails': seatDetails,
            'seatInfos': seatInfos,
            'segmentInfos': segmentInfos,
            'rewardInfos': rewardInfos,
            'recoverInfos': recoverInfos,
            'winStreakRewardInfos': winStreakRewardInfos,
            'treasureChestInfos': treasureChestInfos
        }

    def sendWinloseRes(self, result):
        details = self.buildResultDetails(result)
        mp = self.buildWinloseRes(result, details, 1)
        from dizhu.game import TGDizhu
        from dizhu.entity.common.events import ActiveEvent
        crossPlayCount = configure.getGameJson(DIZHU_GAMEID, 'wx.cross', {}).get('crossPlayCount', 10)
        crossDelaySeconds = configure.getGameJson(DIZHU_GAMEID, 'wx.cross', {}).get('crossDelaySeconds', 10)
        authPlayCount = configure.getGameJson(DIZHU_GAMEID, 'authorization', {}).get('authPlayCount', 5)
        rewards = configure.getGameJson(DIZHU_GAMEID, 'authorization', {}).get('rewards', {})
        for index, seat in enumerate(self.table.seats):
            if seat.player and not seat.isGiveup:

                ssts = result.seatStatements

                # 分享时的二维码等信息
                mp.setResult('share', commconf.getNewShareInfoByCondiction(self.gameId, seat.player.clientId, 'winstreak'))

                # 是否达到踢出值
                mp.setResult('isKickOutCoin', 0)

                # 服务费字段
                mp.setResult('room_fee', ssts[index].fee + ssts[index].fixedFee)

                mp.rmResult('segmentInfo')
                mp.setResult('segmentInfo', details['segmentInfos'][index])

                mp.rmResult('gameWinReward')
                if details['rewardInfos'][index]:
                    mp.setResult('gameWinReward', details['rewardInfos'][index])
                # 判断复活条件
                mp.rmResult('recover')
                recover = details['recoverInfos'][index]
                if recover:
                    mp.setResult('recover', recover)

                # 连胜任务信息
                mp.rmResult('winStreakInfo')
                mp.setResult('winStreakInfo', details['winStreakRewardInfos'][index])

                # 连胜宝箱
                mp.rmResult('treasureChestInfo')
                mp.setResult('treasureChestInfo', details['treasureChestInfos'][index])

                # 是否展示交叉导流
                dailyPlayCount = new_table_remote.doGetUserDailyPlayCount(seat.userId, DIZHU_GAMEID)
                mp.setResult('dailyPlay', dailyPlayCount)
                mp.rmResult('showCross')
                mp.setResult('showCross', dailyPlayCount > crossPlayCount)
                mp.setResult('crossDelaySeconds', crossDelaySeconds)
                if ftlog.is_debug():
                    ftlog.debug('sendWinloseRes userId=', seat.userId,
                                'dailyPlayCount=', dailyPlayCount,
                                'showCross=', dailyPlayCount > crossPlayCount,
                                'crossDelaySeconds=', crossDelaySeconds)

                if dailyPlayCount == 3:
                    TGDizhu.getEventBus().publishEvent(ActiveEvent(6, seat.userId, 'playTimes3'))

                mp.rmResult('auth')
                if dailyPlayCount == authPlayCount:
                    mp.setResult('auth', {'auth': 1, 'rewards': rewards})

                # 每日首胜
                if seat.player.isFirstWin(ssts[index].isWin):
                    from dizhu.game import TGDizhu
                    from dizhu.entity.common.events import ActiveEvent
                    import poker.util.timestamp as pktimestamp
                    TGDizhu.getEventBus().publishEvent(ActiveEvent(6, seat.userId, 'dailyFirstWin'))
                    today = pktimestamp.formatTimeDayInt()
                    firstWin = {str(today): 1}
                    gamedata.setGameAttrs(seat.userId, DIZHU_GAMEID, ['firstWin'], [strutil.dumps(firstWin)])

                if ftlog.is_debug():
                    ftlog.debug('DizhuTableProtoSegment.sendWinloseRes userId=', seat.userId,
                                'mp=', mp._ht)
                router.sendToUser(mp, seat.userId)

    def _onGameStart(self, event):
        if ftlog.is_debug():
            ftlog.debug('DizhuTableProtoSegment._onGameStart',
                        'tableId=', event.table.tableId,
                        'seats=', [(s.userId, s.seatId) for s in event.table.seats])
        for seat in event.table.seats:
            seat.player.returnFeesFlag = 0
            task_remote.doSyncUserWinStreakBackUp(seat.userId)
        self.sendGameStartResAll()

